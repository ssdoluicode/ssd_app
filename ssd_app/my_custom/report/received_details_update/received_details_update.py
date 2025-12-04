# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    filters = filters or {}
    status_filter = filters.get("status", "Pending")  # default Pending

    # Build WHERE clause based on status
    where_clause = ""
    if status_filter == "Pending":
        where_clause = "WHERE rec.rec_details != 1"
    elif status_filter == "Updated":
        where_clause = "WHERE rec.rec_details = 1"
    # "All" -> no WHERE clause

    query = f"""
       SELECT 
            rec.name,
            cif.inv_no, 
            rec.received_date,
            cif.inv_date, 
            cus.customer, 
            noti.notify, 
            bank.bank,
            IF(cif.payment_term IN ('LC', 'DA'),
                CONCAT(cif.payment_term, '- ', cif.term_days),
                cif.payment_term
            ) AS p_term,
            cif.document,
            rec.received,
            rec.rec_details
        FROM `tabDoc Received` rec
        LEFT JOIN `tabCIF Sheet` cif ON cif.name = rec.inv_no
        LEFT JOIN `tabCustomer` cus ON cus.name = rec.customer
        LEFT JOIN `tabNotify` noti ON noti.name = rec.notify
        LEFT JOIN `tabBank` bank ON bank.name = rec.bank
		{where_clause}
		ORDER BY rec.received_date DESC
    """

    data = frappe.db.sql(query, as_dict=1)

    columns = [
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 125},
        {"label": "Inv Date", "fieldname": "inv_date", "fieldtype": "Date", "width": 110},
        {"label": "Rec Date", "fieldname": "received_date", "fieldtype": "Date", "width": 110},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 250},
        {"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 250},
        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 70},
        {"label": "P Term", "fieldname": "p_term", "fieldtype": "Data", "width": 95},
        {"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 125},
        {"label": "Rec Amnt", "fieldname": "received", "fieldtype": "Float", "width": 125},
    ]

    return columns, data
