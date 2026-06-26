import frappe
import numpy as np
import pandas as pd
from ssd_app.my_custom.report.tally_entry.tally_entry import execute
from frappe.utils import flt


@frappe.whitelist()
def create_tally_xml(filters):
    filters = frappe.parse_json(filters)

    # 1. Fetch Report Data
    columns, data = execute(filters)

    # Early exit: If report data is completely empty
    if not data:
        frappe.msgprint("No report data found for the selected filters.")
        return {"status": "failed", "report_rows": 0}

    company = filters.get("company")
    company_code = frappe.db.get_value("Company", company, "number_code")

    if not company_code:
        frappe.throw(
            f"Number code not found for company: {company}. Please configure it."
        )

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
        if row.get("document") and not row.get("direct_to_supplier"):
            if not row.get("customer_doc"):
                error_msg= f"In Inv no {row.get('inv_no')} Customer Doc A/C Missing"
                frappe.throw(error_msg)
        if flt(row.get("CC"), 2) !=0:
            if not row.get("customer_cc"):
                error_msg= f"In Inv no {row.get('inv_no')} Customer CC A/C Missing"
                frappe.throw(error_msg)


    # 6. Output to file
    merged_df.to_excel("temp.xlsx", index=False)

    return {
        "status": "success",
        "report_rows": len(merged_df),
    }

