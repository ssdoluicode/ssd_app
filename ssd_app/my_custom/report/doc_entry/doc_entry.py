# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe



def execute(filters=None):
    filters = filters or {}
    status_filter = filters.get("status", "Pending")  # default Pending

    # Build WHERE clause based on status
    where_clause_nego = ""
    if status_filter == "Pending":
        where_clause_nego = "WHERE nego.nego_details != 1"
    elif status_filter == "Updated":
        where_clause_nego = "WHERE nego.nego_details = 1"
        
    where_clause_ref = ""
    if status_filter == "Pending":
        where_clause_ref = "WHERE ref.refund_details != 1"
    elif status_filter == "Updated":
        where_clause_ref = "WHERE ref.refund_details = 1"
        
    where_clause_rec = ""
    if status_filter == "Pending":
        where_clause_rec = "WHERE rec.rec_details != 1"
    elif status_filter == "Updated":
        where_clause_rec = "WHERE rec.rec_details = 1"
    

    query = f"""
		SELECT *
		FROM (
			SELECT 
				nego.name,
				cif.inv_no, 
				nego.nego_date AS date,
				"Nego" AS type,
				cif.inv_date, 
				cus.customer, 
				noti.notify, 
				bank.bank,
				IF(cif.payment_term IN ('LC', 'DA'),
					CONCAT(cif.payment_term, '- ', cif.term_days),
					cif.payment_term
				) AS p_term,
				cif.document,
				nego.nego_amount AS amount,
				nego.nego_details AS details
			FROM `tabDoc Nego` nego
			LEFT JOIN `tabCIF Sheet` cif ON cif.name = nego.inv_no
			LEFT JOIN `tabCustomer` cus ON cus.name = cif.customer
			LEFT JOIN `tabNotify` noti ON noti.name = cif.notify
			LEFT JOIN `tabBank` bank ON bank.name = cif.bank
			{where_clause_nego}

			UNION ALL
			
			SELECT 
				ref.name,
				cif.inv_no, 
				ref.refund_date AS date,
				"Refund" AS type,
				cif.inv_date, 
				cus.customer, 
				noti.notify, 
				bank.bank,
				IF(cif.payment_term IN ('LC', 'DA'),
					CONCAT(cif.payment_term, '- ', cif.term_days),
					cif.payment_term
				) AS p_term,
				cif.document,
				ref.refund_amount AS amount,
				ref.refund_details AS details
			FROM `tabDoc Refund` ref
			LEFT JOIN `tabCIF Sheet` cif ON cif.name = ref.inv_no
			LEFT JOIN `tabCustomer` cus ON cus.name = cif.customer
			LEFT JOIN `tabNotify` noti ON noti.name = cif.notify
			LEFT JOIN `tabBank` bank ON bank.name = cif.bank
			{where_clause_ref}

			UNION ALL
			
			SELECT 
				rec.name,
				cif.inv_no, 
				rec.received_date AS date,
				"Received" AS type,
				cif.inv_date, 
				cus.customer, 
				noti.notify, 
				bank.bank,
				IF(cif.payment_term IN ('LC', 'DA'),
					CONCAT(cif.payment_term, '- ', cif.term_days),
					cif.payment_term
				) AS p_term,
				cif.document,
				rec.received AS amount,
				rec.rec_details AS details
			FROM `tabDoc Received` rec
			LEFT JOIN `tabCIF Sheet` cif ON cif.name = rec.inv_no
			LEFT JOIN `tabCustomer` cus ON cus.name = cif.customer
			LEFT JOIN `tabNotify` noti ON noti.name = cif.notify
			LEFT JOIN `tabBank` bank ON bank.name = cif.bank
			{where_clause_rec}
		) AS all_data
		ORDER BY date
	"""


    data = frappe.db.sql(query, as_dict=1)

    columns = [
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 125},
        {"label": "Inv Date", "fieldname": "inv_date", "fieldtype": "Date", "width": 110},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 250},
        {"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 250},
        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 70},
        {"label": "P Term", "fieldname": "p_term", "fieldtype": "Data", "width": 95},
        {"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 125},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Float", "width": 125},
        {"label": "Type", "fieldname": "type", "fieldtype": "Data", "width": 125},
    ]

    return columns, data
