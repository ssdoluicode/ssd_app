# # Copyright (c) 2025, SSDolui and contributors
# # For license information, please see license.txt

import frappe

def execute(filters=None):
    filters = filters or {}
    status_filter = filters.get("status", "Pending")  # default Pending

    # Build WHERE clause based on status
    where_clause = ""
    if status_filter == "Pending":
        where_clause = "WHERE nego.nego_details != 1"
    elif status_filter == "Updated":
        where_clause = "WHERE nego.nego_details = 1"
    # "All" -> no WHERE clause

    query = f"""
        SELECT 
            nego.name,
            cif.inv_no, 
            cif.inv_date, 
            cus.customer, 
            noti.notify, 
            bank.bank,
            IF(cif.payment_term IN ('LC', 'DA'),
                CONCAT(cif.payment_term, '- ', cif.term_days),
                cif.payment_term
            ) AS p_term,
            cif.document,
            nego.nego_amount,
            nego.nego_details
        FROM `tabDoc Nego` nego
        LEFT JOIN `tabCIF Sheet` cif ON cif.name = nego.inv_no
        LEFT JOIN `tabCustomer` cus ON cus.name = nego.customer
        LEFT JOIN `tabNotify` noti ON noti.name = nego.notify
        LEFT JOIN `tabBank` bank ON bank.name = nego.bank
        {where_clause}
		ORDER BY nego.nego_date DESC
    """

    data = frappe.db.sql(query, as_dict=1)

    columns = [
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 125},
        {"label": "Inv Date", "fieldname": "inv_date", "fieldtype": "Date", "width": 110},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 250},
        {"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 250},
        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 70},
        {"label": "P Term", "fieldname": "p_term", "fieldtype": "Data", "width": 75},
        {"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 125},
        {"label": "Nego Amnt", "fieldname": "nego_amount", "fieldtype": "Float", "width": 125},
    ]

    return columns, data
