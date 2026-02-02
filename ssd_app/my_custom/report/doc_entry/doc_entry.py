# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe



def execute(filters=None):
    filters = filters or {}
    status_filter = filters.get("status", "Pending")   # default Pending
    type_filter = filters.get("type", "All")           # default All

    # Build WHERE clause based on status
    where_clause_nego = "WHERE 1=1"
    where_clause_ref = "WHERE 1=1"
    where_clause_rec = "WHERE 1=1"

    # Status filter
    if status_filter == "Pending":
        where_clause_nego += " AND nego.nego_details != 1"
        where_clause_ref += " AND ref.refund_details != 1"
        where_clause_rec += " AND rec.rec_details != 1"

    elif status_filter == "Updated":
        where_clause_nego += " AND nego.nego_details = 1"
        where_clause_ref += " AND ref.refund_details = 1"
        where_clause_rec += " AND rec.rec_details = 1"

    # Type filter (show only selected table)
    if type_filter == "Nego":
        where_clause_nego += " AND 1=1"
        where_clause_ref += " AND 1=0"
        where_clause_rec += " AND 1=0"

    elif type_filter == "Refund":
        where_clause_nego += " AND 1=0"
        where_clause_ref += " AND 1=1"
        where_clause_rec += " AND 1=0"

    elif type_filter == "Received":
        where_clause_nego += " AND 1=0"
        where_clause_ref += " AND 1=0"
        where_clause_rec += " AND 1=1"
	

	# Build WHERE clause based on status
  

    query = f"""
		SELECT *
		FROM (
			SELECT
				sb.name AS cif_id,
				nego.name,
				sb.inv_no, 
				nego.nego_date AS date,
				"Nego" AS type,
				cus.customer, 
				noti.notify, 
				bank.bank,
				IF(pt.term_name IN ('LC', 'DA'),
					CONCAT(pt.term_name, '- ', sb.term_days),
					pt.term_name
				) AS p_term,
				sb.document,
				nego.nego_amount AS amount,
				nego.nego_details AS details
			FROM `tabDoc Nego` nego
            LEFT JOIN `tabShipping Book` sb ON sb.name = nego.shipping_id
            LEFT JOIN `tabPayment Term` pt ON pt.name= sb.payment_term
			LEFT JOIN `tabCustomer` cus ON cus.name = sb.customer
			LEFT JOIN `tabNotify` noti ON noti.name = sb.notify
			LEFT JOIN `tabBank` bank ON bank.name = sb.bank
			{where_clause_nego}

			UNION ALL
			
			SELECT 
				sb.name AS cif_id,
				ref.name,
				sb.inv_no, 
				ref.refund_date AS date,
				"Refund" AS type,
				cus.customer, 
				noti.notify, 
				bank.bank,
				IF(sb.payment_term IN ('LC', 'DA'),
					CONCAT(pt.term_name, '- ', sb.term_days),
					pt.term_name
				) AS p_term,
				sb.document,
				ref.refund_amount AS amount,
				ref.refund_details AS details
			FROM `tabDoc Refund` ref
            LEFT JOIN `tabShipping Book` sb ON sb.name = ref.shipping_id
            LEFT JOIN `tabPayment Term` pt ON pt.name= sb.payment_term
			LEFT JOIN `tabCustomer` cus ON cus.name = sb.customer
			LEFT JOIN `tabNotify` noti ON noti.name =sb.notify
			LEFT JOIN `tabBank` bank ON bank.name = sb.bank
			{where_clause_ref}

			UNION ALL
			
			SELECT 
				sb.name AS cif_id,
				rec.name,
				sb.inv_no, 
				rec.received_date AS date,
				"Received" AS type,
				cus.customer, 
				noti.notify, 
				bank.bank,
				IF(pt.term_name IN ('LC', 'DA'),
					CONCAT(pt.term_name, '- ', sb.term_days),
					pt.term_name
				) AS p_term,
				sb.document,
				rec.received AS amount,
				rec.rec_details AS details
			FROM `tabDoc Received` rec
            LEFT JOIN `tabShipping Book` sb ON sb.name = rec.shipping_id
            LEFT JOIN `tabPayment Term` pt ON pt.name= sb.payment_term
			LEFT JOIN `tabCustomer` cus ON cus.name = sb.customer
			LEFT JOIN `tabNotify` noti ON noti.name = sb.notify
			LEFT JOIN `tabBank` bank ON bank.name = sb.bank
			{where_clause_rec}
		) AS all_data
		ORDER BY date
	"""


    data = frappe.db.sql(query, as_dict=1)

    columns = [
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 125},
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
