# # Copyright (c) 2025, SSDolui and contributors
# # For license information, please see license.txt

# import frappe


# def execute(filters=None):
#     filters = filters or {}

#     conditions = []
#     sql_filters = {}

#     if filters.get("from_date"):
#         conditions.append("dnd.nego_date >= %(from_date)s")
#         sql_filters["from_date"] = filters["from_date"]

#     if filters.get("to_date"):
#         conditions.append("dnd.nego_date <= %(to_date)s")
#         sql_filters["to_date"] = filters["to_date"]

#     if filters.get("company"):
#         conditions.append("cif.shipping_company = %(company)s")
#         sql_filters["company"] = filters["company"]

#     # This block only returns Doc Nego entries
#     # if filters.get("entry_for") and filters["entry_for"] != "Doc Nego":
#     #     conditions.append("1 = 0")  # safely exclude this block


#     where_clause = ""
#     if conditions:
#         where_clause = "WHERE " + " AND ".join(conditions)

#     query = f"""
#         SELECT 
#             dnd.invoice_no AS inv_no,
#             dnd.nego_date AS date,
#             com.company_code AS com,
#             noti.code AS notify_party,
#             dnd.payment_term AS payment_term,
#             bank.bank AS bank,

#             CAST(IFNULL(dnd.nego_amount, 0) AS DECIMAL(18,2)) AS nego_amount,
#             CAST(IFNULL(dnd.interest, 0) AS DECIMAL(18,2)) AS interest,

#             CAST(
#                 IFNULL(dnd.nego_amount, 0)
#                 - IFNULL(dnd.interest, 0)
#                 - IFNULL(dnd.bank_amount, 0)
#             AS DECIMAL(18,2)) AS bank_charge,

#             CAST(IFNULL(dnd.bank_amount, 0) AS DECIMAL(18,2)) AS bank_amount,

#             "" AS ref_no
#         FROM `tabDoc Nego Details` dnd
#         LEFT JOIN `tabCIF SHEET` cif ON cif.name = dnd.cif_id
#         LEFT JOIN `tabBank` bank ON bank.name = cif.bank
#         LEFT JOIN `tabNotify` noti ON noti.name = cif.notify
#         LEFT JOIN `tabCompany` com ON com.name = cif.shipping_company
#         {where_clause}
#         ORDER BY dnd.nego_date ASC
#     """

#     data = frappe.db.sql(query, sql_filters, as_dict=1)

#     columns = [
#         {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
#         {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
#         {"label": "Com", "fieldname": "com", "fieldtype": "Data", "width": 110},
#         {"label": "Notify Party", "fieldname": "notify_party", "fieldtype": "Data", "width": 250},
#         {"label": "Payment Term", "fieldname": "payment_term", "fieldtype": "Data", "width": 130},
#         {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 110},
#         {"label": "Nego Amount", "fieldname": "nego_amount", "fieldtype": "Float", "width": 130},
#         {"label": "Interest", "fieldname": "interest", "fieldtype": "Float", "width": 110},
#         {"label": "Bank Charge", "fieldname": "bank_charge", "fieldtype": "Float", "width": 130},
#         {"label": "Bank Amount", "fieldname": "bank_amount", "fieldtype": "Float", "width": 130},
#         {"label": "Ref No", "fieldname": "ref_no", "fieldtype": "Data", "width": 90}
#     ]

#     return columns, data


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

    # elif entry_for == "LC Payment":
    #     return execute_lc_payment(filters)

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
# Doc Nego
# ---------------------------------------
def execute_doc_nego(filters):
    conditions, sql_filters = build_conditions(filters, "dnd.nego_date", "cif.shipping_company")
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT 
            dnd.invoice_no AS inv_no,
            dnd.nego_date AS date,
            com.company_code AS com,
            noti.code AS notify_party,
            dnd.payment_term AS payment_term,
            bank.bank AS bank,
            CAST(IFNULL(dnd.nego_amount, 0) AS DECIMAL(18,2)) AS nego_amount,
            CAST(IFNULL(dnd.interest, 0) AS DECIMAL(18,2)) AS interest,
            CAST(IFNULL(dnd.nego_amount,0) - IFNULL(dnd.interest,0) - IFNULL(dnd.bank_amount,0) AS DECIMAL(18,2)) AS bank_charge,
            CAST(IFNULL(dnd.bank_amount, 0) AS DECIMAL(18,2)) AS bank_amount,
            "" AS ref_no
        FROM `tabDoc Nego Details` dnd
        LEFT JOIN `tabCIF SHEET` cif ON cif.name = dnd.cif_id
        LEFT JOIN `tabBank` bank ON bank.name = cif.bank
        LEFT JOIN `tabNotify` noti ON noti.name = cif.notify
        LEFT JOIN `tabCompany` com ON com.name = cif.shipping_company
        {where_clause}
        ORDER BY dnd.nego_date ASC
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
    conditions, sql_filters = build_conditions(filters, "dnd.nego_date", "cif.shipping_company")
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT 
            dnd.invoice_no AS inv_no,
            dnd.nego_date AS date,
            com.company_code AS com,
            noti.code AS notify_party,
            dnd.payment_term AS payment_term,
            bank.bank AS bank,
            CAST(IFNULL(dnd.nego_amount, 0) AS DECIMAL(18,2)) AS nego_amount,
            CAST(IFNULL(dnd.interest, 0) AS DECIMAL(18,2)) AS interest,
            CAST(IFNULL(dnd.nego_amount,0) - IFNULL(dnd.interest,0) - IFNULL(dnd.bank_amount,0) AS DECIMAL(18,2)) AS bank_charge,
            CAST(IFNULL(dnd.bank_amount, 0) AS DECIMAL(18,2)) AS bank_amount,
            "" AS ref_no
        FROM `tabDoc Nego Details` dnd
        LEFT JOIN `tabCIF SHEET` cif ON cif.name = dnd.cif_id
        LEFT JOIN `tabBank` bank ON bank.name = cif.bank
        LEFT JOIN `tabNotify` noti ON noti.name = cif.notify
        LEFT JOIN `tabCompany` com ON com.name = cif.shipping_company
        {where_clause}
        ORDER BY dnd.nego_date ASC
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


