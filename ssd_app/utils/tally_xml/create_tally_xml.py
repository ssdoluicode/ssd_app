import frappe
import numpy as np
import re
import pandas as pd
from ssd_app.my_custom.report.tally_entry.tally_entry import execute_sales, execute_cc_received, execute_doc_nego, execute_doc_refund, execute_doc_received

from ssd_app.utils.tally_xml.generate_xml import GenerateTallyXML
from frappe.utils import flt
from frappe.utils import today


@frappe.whitelist()
def create_tally_xml(filters):
    filters = frappe.parse_json(filters)
    entry_for = filters.get("entry_for")
    company = filters.get("company")
    company_code = frappe.db.get_value("Company", company, "number_code")
    comp_name = frappe.db.get_value("Company", company, "company_code")
    safe_comp_name = re.sub(r'[^\w]', '_', comp_name)
    safe_comp_name = re.sub(r'_+', '_', safe_comp_name).strip('_')
    gen_xml= GenerateTallyXML(int(company_code))
    cost_center_already_in_tally= frappe.get_all("Cost Center in Tally", filters={"company": company}, pluck="invoice_no")
    sales_already_in_tally= frappe.get_all("Sales Entry Done in Tally", filters={"company": company}, pluck="invoice_no")

    if entry_for == "Sales":
        xml_df= sales_entry_df(filters)
        all_invoices = xml_df['inv_no'].dropna().unique().tolist()
        cost_center_need_to_create= []
        for i in all_invoices:
            if i not in cost_center_already_in_tally:
                cost_center_need_to_create.append(i)
            if i in sales_already_in_tally:
                frappe.throw(f"Sales entry of inv no {i} already in tally")

        
        sales_xml= gen_xml.generate_sales_entry_xml(xml_df)
        data_context= [
            {"file_name": f"sales_xml_{safe_comp_name}", "data":sales_xml, "alert_msg":f"Sales XML Generate for {len(xml_df)} inv"}
            ]
        for row in xml_df.itertuples():
            frappe.get_doc({
                        "doctype": "Sales Entry Done in Tally",
                        "inv_no": row.cif_id,
                        "company": company,
                        "entry_date": today()
                    }).insert(ignore_permissions=True)
        cost_center_need_to_create= [inv_no for inv_no in all_invoices if inv_no not in cost_center_already_in_tally]

        if cost_center_need_to_create:
            cost_center_xml = gen_xml.generate_create_cost_center_xml(cost_center_need_to_create)
        
            data_context.insert(0,{"file_name": f"cost_center_xml_{safe_comp_name}", "data":cost_center_xml, "alert_msg":f"Cost Center XML Generate for {len(cost_center_need_to_create)} inv"})
        
            for row in xml_df.itertuples():
                if (row.inv_no in cost_center_need_to_create):
                    frappe.get_doc({
                                "doctype": "Cost Center in Tally",
                                "inv_no": row.cif_id,
                                "company": company,
                                "entry_date": today()
                            }).insert(ignore_permissions=True)

    elif entry_for == "CC Received":
        xml_df= cc_rec_entry_df(filters)
        tally_entry_xml= gen_xml.generate_cc_received_xml(xml_df, rec_ref_no = filters.get("rec_ref_no"))
        data_context= [
            {"file_name": f"cc_rec_entry_xml_{safe_comp_name}", "data":tally_entry_xml, "alert_msg":f"CC Received XML Generate for {len(xml_df)} Entries"}
            ]
        
    
    elif entry_for == "Doc Nego":
        xml_df= doc_nego_entry_df(filters)
        tally_entry_xml= gen_xml.generate_doc_nego_xml(xml_df, rec_ref_no = filters.get("rec_ref_no"))
        data_context= [
            {"file_name": f"doc_nego_entry_xml_{safe_comp_name}", "data":tally_entry_xml, "alert_msg":f"Doc Nego XML Generate for {len(xml_df)} Entries"}
            ]
        
    elif entry_for == "Doc Refund":
        xml_df= doc_refund_entry_df(filters)
        tally_entry_xml= gen_xml.generate_doc_ref_xml(xml_df, pay_ref_no = filters.get("pay_ref_no"))
        data_context= [
            {"file_name": f"doc_refund_entry_xml_{safe_comp_name}", "data":tally_entry_xml, "alert_msg":f"Doc Refund  XML Generate for {len(xml_df)} Entries"}
            ]
    
    elif entry_for == "Doc Received":
        xml_df= doc_rec_entry_df(filters)
        tally_entry_xml= gen_xml.generate_doc_rec_xml(xml_df, com= company,  rec_ref_no = filters.get("rec_ref_no"), pay_ref_no = filters.get("pay_ref_no"), jv_ref_no = filters.get("jv_ref_no"))
        data_context= [
            {"file_name": f"doc_rec_entry_xml_{safe_comp_name}", "data":tally_entry_xml, "alert_msg":f"Doc Rec XML Generate for {len(xml_df)} Entries"}
            ]
        china_xml_df = xml_df[xml_df["acc_com_id"] != company].copy()
        china_xml_df= china_xml_df[["date", "inv_no", "notify_party", "customer_doc_9", "rec_amount"]]
        int_com_map= {2:"UXL- Taiwan (CC)", 3: "Tunwa Inds. (CC)", 8 : "GDI (CC)", 9 : "UXL- China (CC)"}
        tally_entry_xml_china= gen_xml.generate_doc_rec_xml_china(china_xml_df, int_com=int_com_map[company_code])
        data_context.insert(0,{"file_name": f"doc_rec_entry_xml_uxl-china", "data":tally_entry_xml_china, "alert_msg":f"Doc Received XML Generate for {len(china_xml_df)} inv in China"})
        


    return {
        "status": "success",
        "data_context": data_context,
    }

@frappe.whitelist()
def sales_entry_df(filters):
    # 1. Fetch Report Data
    columns, data = execute_sales(filters)

    # Early exit: If report data is completely empty
    if not data:
        frappe.msgprint("No report data found for the selected filters.")
        return {"status": "failed", "report_rows": 0}

    company = filters.get("company")
    company_code = frappe.db.get_value("Company", company, "number_code")

    if not company_code:
        frappe.throw(f"Number code not found for company: {company}. Please configure it.")

    # 2. Fetch Master Maps
    customer_data = frappe.db.sql(
        f"""
        SELECT
            cus_tn.customer_id AS cus_id,
            cus_tn.company_{company_code}_doc AS customer_doc,
            cus_tn.company_{company_code}_cc AS customer_cc
        FROM `tabCustomer Tally Name` cus_tn
        """,
        as_dict=True,
    )

    category_data = frappe.db.sql(
        """
        SELECT cat.name AS cat_id, cat.sales_head_in_tally AS sales_head
        FROM `tabProduct Category` cat
        """,
        as_dict=True,
    )

    # Early exit: Validate master records exist
    if not customer_data or not category_data:
        frappe.throw(
            "Missing master data mapping setup in Customer Tally Name or Product Category tables."
        )

    # 3. Clean and Build DataFrames (Using list comprehension to fix __array_struct__ error)
    data_df = pd.DataFrame([dict(row) for row in data])
    customer_df = pd.DataFrame([dict(row) for row in customer_data])
    category_df = pd.DataFrame([dict(row) for row in category_data])

    # 4. Perform Left Merges
    merged_df = pd.merge(data_df, customer_df, on="cus_id", how="left")
    merged_df = pd.merge(merged_df, category_df, on="cat_id", how="left")

    # 5. Fast Country-based Suffix Rule
    if "sales_head" in merged_df.columns:
        country_series = merged_df["country"].fillna("").astype(str).str.strip()
        sales_head_series = (
            merged_df["sales_head"].fillna("").astype(str).str.strip()
        )

        merged_df["sales_head"] = np.where(
            country_series == "India",
            sales_head_series + " India",
            sales_head_series + " Others",
        )
    # 6. Row-by-Row Validation Loop
    records = merged_df.to_dict(orient="records")
    for row in records:
        if row.get("document") and not row.get("dir_to_sup"):
            if not row.get("customer_doc"):
                error_msg= f"In Inv no {row.get('inv_no')} Customer Doc A/C Missing"
                frappe.throw(error_msg)
        if flt(row.get("CC"), 2) !=0:
            if not row.get("customer_cc"):
                error_msg= f"In Inv no {row.get('inv_no')} Customer CC A/C Missing"
                frappe.throw(error_msg)

    return merged_df


@frappe.whitelist()
def cc_rec_entry_df(filters):
    # 1. Fetch Report Data
    columns, data = execute_cc_received(filters)

    # Early exit: If report data is completely empty
    if not data:
        frappe.msgprint("No report data found for the selected filters.")
        return {"status": "failed", "report_rows": 0}

    company = filters.get("company")
    company_code = frappe.db.get_value("Company", company, "number_code")

    if not company_code:
        frappe.throw(f"Number code not found for company: {company}. Please configure it.")

    # 2. Fetch Master Maps
    bank_data = frappe.db.sql(
        f"""
        SELECT
            bank_tn.bank_id AS bank_id,
            bank_tn.company_{company_code}_bank AS bank_name
        FROM `tabBank Name in Tally` bank_tn
        """,
        as_dict=True,
    )

    customer_data = frappe.db.sql(
        f"""
        SELECT
            cus_tn.customer_id AS cus_id,
            cus_tn.company_{company_code}_cc AS customer_cc
        FROM `tabCustomer Tally Name` cus_tn
        """,
        as_dict=True,
    )

    # 3. Clean and Build DataFrames (Using list comprehension to fix __array_struct__ error)
    data_df = pd.DataFrame([dict(row) for row in data])
    bank_df = pd.DataFrame([dict(row) for row in bank_data])
    customer_df = pd.DataFrame([dict(row) for row in customer_data])

    # 4. Perform Left Merges
    merged_df = pd.merge(data_df, bank_df, on="bank_id", how="left")
    merged_df = pd.merge(merged_df, customer_df, on="cus_id", how="left")

    # 5. Row-by-Row Validation Loop
    records = merged_df.to_dict(orient="records")
    for row in records:
        if not row.get("customer_cc"):
            error_msg= f"In Customer CC A/C Missing of {row.get('customer')}"
            frappe.throw(error_msg)
        if not row.get("bank_name"):
            error_msg= f" Bank A/C Missing in {row.get('bank')} Bank"
            frappe.throw(error_msg)

    return merged_df


@frappe.whitelist()
def doc_nego_entry_df(filters):
    # 1. Fetch Report Data
    columns, data = execute_doc_nego(filters)

    # Early exit: If report data is completely empty
    if not data:
        frappe.msgprint("No report data found for the selected filters.")
        return {"status": "failed", "report_rows": 0}

    company = filters.get("company")
    company_code = frappe.db.get_value("Company", company, "number_code")

    if not company_code:
        frappe.throw(f"Number code not found for company: {company}. Please configure it.")

    # 2. Fetch Master Maps
    bank_data = frappe.db.sql(
        f"""
        SELECT
            bank_tn.bank_id AS bank_id,
            bank_tn.company_{company_code}_bank AS bank_name,
            bank_tn.company_{company_code}_nego AS bank_dpda
        FROM `tabBank Name in Tally` bank_tn
        """,
        as_dict=True,
    )


    # 3. Clean and Build DataFrames (Using list comprehension to fix __array_struct__ error)
    data_df = pd.DataFrame([dict(row) for row in data])
    bank_df = pd.DataFrame([dict(row) for row in bank_data])
    
    # 4. Perform Left Merges
    merged_df = pd.merge(data_df, bank_df, on="bank_id", how="left")
   
    # 5. Row-by-Row Validation Loop
    records = merged_df.to_dict(orient="records")
    for row in records:
        if not row.get("bank_dpda"):
            error_msg= f"In Bank DP DA A/C Missing of {row.get('bank')}"
            frappe.throw(error_msg)
        if not row.get("bank_name"):
            error_msg= f" Bank A/C Missing in {row.get('bank')} Bank"
            frappe.throw(error_msg)
    return merged_df



@frappe.whitelist()
def doc_refund_entry_df(filters):
    # 1. Fetch Report Data
    columns, data = execute_doc_refund(filters)

    # Early exit: If report data is completely empty
    if not data:
        frappe.msgprint("No report data found for the selected filters.")
        return {"status": "failed", "report_rows": 0}

    company = filters.get("company")
    company_code = frappe.db.get_value("Company", company, "number_code")

    if not company_code:
        frappe.throw(f"Number code not found for company: {company}. Please configure it.")

    # 2. Fetch Master Maps
    bank_data = frappe.db.sql(
        f"""
        SELECT
            bank_tn.bank_id AS bank_id,
            bank_tn.company_{company_code}_bank AS bank_name,
            bank_tn.company_{company_code}_nego AS bank_dpda
        FROM `tabBank Name in Tally` bank_tn
        """,
        as_dict=True,
    )

    # 3. Clean and Build DataFrames (Using list comprehension to fix __array_struct__ error)
    data_df = pd.DataFrame([dict(row) for row in data])
    bank_df = pd.DataFrame([dict(row) for row in bank_data])
    
    # 4. Perform Left Merges
    merged_df = pd.merge(data_df, bank_df, on="bank_id", how="left")
   
    # 5. Row-by-Row Validation Loop
    records = merged_df.to_dict(orient="records")
    for row in records:
        if not row.get("bank_dpda"):
            error_msg= f"In Bank DP DA A/C Missing of {row.get('bank')}"
            frappe.throw(error_msg)
        if not row.get("bank_name"):
            error_msg= f" Bank A/C Missing in {row.get('bank')} Bank"
            frappe.throw(error_msg)

    return merged_df


@frappe.whitelist()
def doc_rec_entry_df(filters):
    # 1. Fetch Report Data
    columns, data = execute_doc_received(filters)

    # Early exit: If report data is completely empty
    if not data:
        frappe.msgprint("No report data found for the selected filters.")
        return {"status": "failed", "report_rows": 0}

    company = filters.get("company")
    company_code = frappe.db.get_value("Company", company, "number_code")

    if not company_code:
        frappe.throw(f"Number code not found for company: {company}. Please configure it.")

    # 2. Fetch Master Maps
    bank_data = frappe.db.sql(
        f"""
        SELECT
            bank_tn.bank_id AS bank_id,
            bank_tn.company_{company_code}_bank AS bank_name,
            bank_tn.company_{company_code}_nego AS bank_dpda
        FROM `tabBank Name in Tally` bank_tn
        """,
        as_dict=True,
    )

    customer_data = frappe.db.sql(
        f"""
        SELECT
            cus_tn.customer_id AS cus_id,
            cus_tn.company_{company_code}_doc AS customer_doc,
            cus_tn.company_9_doc AS customer_doc_9
        FROM `tabCustomer Tally Name` cus_tn
        """,
        as_dict=True,
    )

    # 3. Clean and Build DataFrames (Using list comprehension to fix __array_struct__ error)
    data_df = pd.DataFrame([dict(row) for row in data])
    bank_df = pd.DataFrame([dict(row) for row in bank_data])
    customer_df = pd.DataFrame([dict(row) for row in customer_data])
    
    # 4. Perform Left Merges
    merged_df = pd.merge(data_df, bank_df, on="bank_id", how="left")
    merged_df = pd.merge(merged_df, customer_df, on="cus_id", how="left")
   
    # 5. Row-by-Row Validation Loop
    records = merged_df.to_dict(orient="records")
    for row in records:
        if not row.get("bank_dpda"):
            error_msg= f"In Bank DP DA A/C Missing of {row.get('bank')}"
            frappe.throw(error_msg)

        if not row.get("bank_name"):
            error_msg= f" Bank A/C Missing in {row.get('bank')} Bank"
            frappe.throw(error_msg)

        if not row.get("customer_doc"):
            if(row.get('acc_com_id') == company):
                error_msg= f"In Inv no {row.get('inv_no')} Customer Doc A/C Missing"
                frappe.throw(error_msg)

        if not row.get("customer_doc_9"):
            if(row.get('acc_com_id') != company):
                error_msg= f"In Inv no {row.get('inv_no')} Customer Doc A/C Missing in UXL- China"
                frappe.throw(error_msg)

    # 6. Output to file
    # merged_df.to_excel("doc ref.xlsx", index=False)
    return merged_df