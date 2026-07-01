# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    filters = filters or {}
    entry_for = filters.get("entry_for")

    if entry_for == "Doc Nego":
        return execute_doc_nego(filters)
    
    elif entry_for == "Doc Refund":
        return execute_doc_refund(filters)
    
    elif entry_for == "Doc Received":
        return execute_doc_received(filters)
    
    elif entry_for == "Interest Payment":
        return execute_interest_payment(filters)

    elif entry_for == "CC Received":
        return execute_cc_received(filters)
    
    elif entry_for == "Sales":
        return execute_sales(filters)

    # elif entry_for == "U LC Payment":
    #     return execute_ulc_payment(filters)

    # elif entry_for == "Import Loan":
    #     return execute_imp_loan(filters)

    # elif entry_for == "Import Loan Payment":
    #     return execute_import_loan_payment(filters)

    else:
        # Default: empty
        return [], []

# ---------------------------------------
# Utility Function: Build Conditions
# ---------------------------------------
def build_conditions(filters, date_field, company_field):
    """
    Returns: (conditions_list, sql_filters_dict)
    """
    conditions = []
    sql_filters = {}

    if filters.get("from_date"):
        conditions.append(f"{date_field} >= %(from_date)s")
        sql_filters["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append(f"{date_field} <= %(to_date)s")
        sql_filters["to_date"] = filters["to_date"]

    if filters.get("company"):
        conditions.append(f"{company_field} = %(company)s")
        sql_filters["company"] = filters["company"]

    return conditions, sql_filters


# ---------------------------------------
# Sales
# ---------------------------------------
def execute_sales(filters):
    conditions, sql_filters = build_conditions(filters, "cif.inv_date", "cif.accounting_company")
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT cif.name AS cif_id, shi.inv_no, shi.customer AS cus_id, cif.inv_date, cus.customer, noti.notify, pcat.product_category, 
        cif.category AS cat_id,
        CAST(ROUND(cif.sales * -1, 2) AS DECIMAL(18,2)) AS sales,
        CAST(ROUND(cif.document, 2) AS DECIMAL(18,2)) AS document,
        CAST(ROUND(cif.cc, 2) AS DECIMAL(18,2)) AS cc,
        pt.term_name AS p_term, pt.direct_to_supplier AS dir_to_sup, noti.country, cif.accounting_company AS acc_com FROM `tabCIF Sheet` cif
        LEFT JOIN `tabShipping Book` shi ON shi.name= cif.inv_no
        LEFT JOIN `tabCustomer` cus ON cus.name= shi.customer
        LEFT JOIN `tabNotify` noti ON shi.notify=noti.name
        LEFT JOIN `tabPayment Term` pt ON pt.name= shi.payment_term
        LEFT JOIN `tabProduct Category` pcat ON pcat.name = cif.category
        {where_clause}
        ORDER BY cif.inv_date ASC
    """
    data= frappe.db.sql(query, sql_filters, as_dict=1)

    columns= [
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
        {"label": "Date", "fieldname": "inv_date", "fieldtype": "Date", "width": 110},
        # {"label": "Com", "fieldname": "com", "fieldtype": "Data", "width": 110},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 200},
        {"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 260},
        {"label": "Category", "fieldname": "product_category", "fieldtype": "Data", "width": 190},
        {"label": "Sales", "fieldname": "sales", "fieldtype": "Float", "width": 110},
        {"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 110},
        {"label": "CC", "fieldname": "cc", "fieldtype": "Float", "width": 110},
        {"label": "P Term", "fieldname": "term_name", "fieldtype": "Data", "width": 100},
        {"label": "Dir To Sup", "fieldname": "dir_to_sup", "fieldtype": "Int", "width": 100},
        {"label": "Country", "fieldname": "country", "fieldtype": "Data", "width": 120},
    ]

    return  columns, data




# ---------------------------------------
# Doc Nego
# ---------------------------------------
def execute_doc_nego(filters):
    conditions, sql_filters = build_conditions(filters, "dn.nego_date", "shi.company")
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT 
            dnd.invoice_no AS inv_no,
            dn.nego_date AS date,
            shi.bank AS bank_id,
            com.company_code AS com,
            noti.code AS notify_party,
            pt.term_name AS payment_term,
            bank.bank AS bank,
            CAST(IFNULL(dn.nego_amount * -1, 0) AS DECIMAL(18,2)) AS nego_amount,
            CAST(IFNULL(dnd.interest, 0) AS DECIMAL(18,2)) AS interest,
            CAST(IFNULL(dn.nego_amount,0) - IFNULL(dnd.interest,0) - IFNULL(dnd.bank_amount,0) AS DECIMAL(18,2)) AS bank_charge,
            CAST(IFNULL(dnd.bank_amount, 0) AS DECIMAL(18,2)) AS bank_amount,
            "" AS ref_no
        FROM `tabDoc Nego Details` dnd
        LEFT JOIN `tabDoc Nego` dn ON dn.name = dnd.inv_no
        LEFT JOIN `tabShipping Book` shi ON shi.name = dn.inv_no
        LEFT JOIN `tabBank` bank ON bank.name = shi.bank
        LEFT JOIN `tabNotify` noti ON noti.name = shi.notify
        LEFT JOIN `tabCompany` com ON com.name =shi.company
        LEFT JOIN `tabPayment Term` pt ON pt.name =shi.payment_term
        {where_clause}
        AND dnd.tally_entry=1
        ORDER BY dn.nego_date ASC
    """
    data= frappe.db.sql(query, sql_filters, as_dict=1)

    columns= [
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
        {"label": "Com", "fieldname": "com", "fieldtype": "Data", "width": 110},
        {"label": "Notify Party", "fieldname": "notify_party", "fieldtype": "Data", "width": 250},
        {"label": "Payment Term", "fieldname": "payment_term", "fieldtype": "Data", "width": 130},
        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 110},
        {"label": "Nego Amount", "fieldname": "nego_amount", "fieldtype": "Float", "width": 130},
        {"label": "Interest", "fieldname": "interest", "fieldtype": "Float", "width": 110},
        {"label": "Bank Charge", "fieldname": "bank_charge", "fieldtype": "Float", "width": 130},
        {"label": "Bank Amount", "fieldname": "bank_amount", "fieldtype": "Float", "width": 130},
        {"label": "Ref No", "fieldname": "ref_no", "fieldtype": "Data", "width": 90}
    ]

    return  columns, data

# ---------------------------------------
# Doc Refund
# ---------------------------------------
def execute_doc_refund(filters):
    conditions, sql_filters = build_conditions(filters, "dr.refund_date", "shi.company")
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT 
            shi.inv_no AS inv_no,
            dr.refund_date AS date,
            com.company_code AS com,
            noti.code AS notify_party,
            shi.bank AS bank_id,
            bank.bank AS bank,

            ROUND(CAST(dr.refund_amount AS DECIMAL(18,2)),2) AS refund_amount,
            ROUND(CAST(drd.interest AS DECIMAL(18,2)),2) AS interest,

            CAST(
                IFNULL(drd.bank_amount, 0)
                - IFNULL(dr.refund_amount, 0)
                - IFNULL(drd.interest, 0)
                AS DECIMAL(18,2)
            ) AS bank_charge,

            ROUND(CAST(drd.bank_amount AS DECIMAL(18,2))*-1,2) AS bank_amount,
            "" AS ref_no
        FROM `tabDoc Refund Details` drd
        LEFT JOIN `tabDoc Refund` dr ON dr.name = drd.inv_no
        LEFT JOIN `tabShipping Book` shi ON shi.name = dr.inv_no
        LEFT JOIN `tabCompany` com ON com.name = shi.company
        LEFT JOIN `tabBank` bank ON bank.name = shi.bank
        LEFT JOIN `tabNotify` noti ON noti.name = shi.notify
        {where_clause}
        AND drd.tally_entry=1
        ORDER BY dr.refund_date ASC
    """
    data= frappe.db.sql(query, sql_filters, as_dict=1)

    columns= [
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
        {"label": "Com", "fieldname": "com", "fieldtype": "Data", "width": 110},
        {"label": "Notify Party", "fieldname": "notify_party", "fieldtype": "Data", "width": 250},
        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 110},
        {"label": "Refund Amount", "fieldname": "refund_amount", "fieldtype": "Float", "width": 130},
        {"label": "Interest", "fieldname": "interest", "fieldtype": "Float", "width": 110},
        {"label": "Bank Charge", "fieldname": "bank_charge", "fieldtype": "Float", "width": 130},
        {"label": "Bank Amount", "fieldname": "bank_amount", "fieldtype": "Float", "width": 130},
        {"label": "Ref No", "fieldname": "ref_no", "fieldtype": "Data", "width": 90}
    ]

    return  columns, data


# ---------------------------------------
# Doc Refund
# ---------------------------------------
def execute_doc_received(filters):
    conditions, sql_filters = build_conditions(filters, "dr.received_date", "shi.company")
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT
            shi.inv_no AS inv_no,
            dr.received_date AS date,
            cus.customer, shi.customer AS cus_id,
            noti.code AS notify_party,
            bank.bank AS bank, shi.bank AS bank_id,
            com.company_code AS shi_com, cif.accounting_company AS acc_com_id,
            a_com.company_code AS acc_com,

            CAST(dr.received AS DECIMAL(18,2))*-1 AS rec_amount,
            CAST(drd.interest AS DECIMAL(18,2)) AS interest,
            CAST(drd.bank_liability AS DECIMAL(18,2)) AS bank_liability,
            CAST(drd.bank_amount AS DECIMAL(18,2)) AS bank_amount,

            CAST(
                dr.received
                - drd.bank_liability
                - drd.interest
                - drd.bank_amount
                AS DECIMAL(18,2)
            ) AS bank_charge,
        "" AS ref_no

        FROM `tabDoc Received Details` drd
        LEFT JOIN `tabDoc Received` dr ON dr.name=drd.inv_no
        LEFT JOIN `tabShipping Book` shi ON shi.name = dr.inv_no
        LEFT JOIN `tabCIF Sheet` cif ON cif.inv_no = dr.shipping_id
        LEFT JOIN `tabCustomer` cus ON cus.name = shi.customer
        LEFT JOIN `tabNotify` noti ON noti.name = shi.notify
        LEFT JOIN `tabBank` bank ON bank.name = shi.bank
        LEFT JOIN `tabCompany` com ON com.name = shi.company
        LEFT JOIN `tabCompany` a_com ON a_com.name = cif.accounting_company
        {where_clause}
        AND drd.tally_entry=1
        ORDER BY dr.received_date ASC
    """
    data= frappe.db.sql(query, sql_filters, as_dict=1)

    columns= [
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
        {"label": "Acc Com", "fieldname": "acc_com", "fieldtype": "Data", "width": 110},
        {"label": "Notify Party", "fieldname": "notify_party", "fieldtype": "Data", "width": 250},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 250},
        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 60},
        {"label": "Rec Amount", "fieldname": "rec_amount", "fieldtype": "Float", "width": 130},
        {"label": "Interest", "fieldname": "interest", "fieldtype": "Float", "width": 110},
        {"label": "Bank Charge", "fieldname": "bank_charge", "fieldtype": "Float", "width": 130},
        {"label": "Bank Liability", "fieldname": "bank_liability", "fieldtype": "Float", "width": 130},
        {"label": "Bank Amount", "fieldname": "bank_amount", "fieldtype": "Float", "width": 130},
        {"label": "Ref No", "fieldname": "ref_no", "fieldtype": "Data", "width": 90}
    ]

    return  columns, data


# ---------------------------------------
# Interest Payment
# ---------------------------------------
def execute_interest_payment(filters):
    conditions, sql_filters = build_conditions(filters, "ip.date", "shi.company")
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT 
        shi.inv_no AS inv_no, ip.date, com.company_code AS com, bank.bank AS bank, 
        CAST(ip.interest AS DECIMAL(18,2)) AS interest,
        CAST(ip.interest AS DECIMAL(18,2))*-1 AS bank_amount,  "" AS ref_no
        FROM `tabInterest Paid` ip
        LEFT JOIN `tabCIF Sheet` cif ON cif.name=ip.cif_id
        LEFT JOIN `tabShipping Book` shi ON shi.name = ip.shipping_id
        LEFT JOIN `tabBank` bank ON bank.name= shi.bank
        LEFT JOIN `tabCompany` com ON com.name= shi.company
        {where_clause}
        AND ip.tally_entry=1
        ORDER BY ip.date ASC
    """
    data= frappe.db.sql(query, sql_filters, as_dict=1)

    columns= [
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
        {"label": "Com", "fieldname": "com", "fieldtype": "Data", "width": 110},
        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 60},
        {"label": "Interest", "fieldname": "interest", "fieldtype": "Float", "width": 110},
        {"label": "Bank Amount ", "fieldname": "bank_amount", "fieldtype": "Float", "width": 120},
        {"label": "Ref No", "fieldname": "ref_no", "fieldtype": "Data", "width": 90}
    ]

    return  columns, data


# ---------------------------------------
# Interest Payment
# ---------------------------------------
def execute_cc_received(filters):
    conditions, sql_filters = build_conditions(filters, "ccr.date", "ccrd.company")
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT 
        ccr.customer AS cus_id,
        cus.customer,
        ccr.date,
        com.company_code AS com,
        ccrd.bank AS bank_id,
        bank.bank,
        CAST(ccrd.amount AS DECIMAL(18,6))*-1 AS cc_received,
        CAST(ccrd.bank_amount AS DECIMAL(18,6)) AS bank_amount,
        CAST(
            IFNULL(ccrd.amount, 0) - IFNULL(ccrd.bank_amount, 0)
            AS DECIMAL(18,6)
        ) AS bank_charge,  "" AS ref_no
    FROM `tabCC Received Details` ccrd
    LEFT JOIN `tabCC Received` ccr
        ON ccr.name = ccrd.cc_received_id
    LEFT JOIN `tabBank` bank
        ON bank.name = ccrd.bank
    LEFT JOIN `tabCompany` com
        ON com.name = ccrd.company
    LEFT JOIN `tabCustomer` cus
        ON cus.name = ccr.customer
        {where_clause} 
        AND ccrd.tally_entry= 1
        ORDER BY ccr.date ASC
    """
    data= frappe.db.sql(query, sql_filters, as_dict=1)

    columns= [
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 200},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
        {"label": "Com", "fieldname": "com", "fieldtype": "Data", "width": 110},
        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 60},
        {"label": "CC Received", "fieldname": "cc_received", "fieldtype": "Float", "width": 110},
        {"label": "Bank Charge", "fieldname": "bank_charge", "fieldtype": "Float", "width": 110},
        {"label": "Bank Amount", "fieldname": "bank_amount", "fieldtype": "Float", "width": 110},
         {"label": "Ref No", "fieldname": "ref_no", "fieldtype": "Data", "width": 90}
    ]

    return  columns, data

