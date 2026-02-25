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
                nego.nego_amount * -1 AS bank_liab,
                (negod.postage_charges + negod.commission + negod.other_charges + negod.round_off) AS bank_ch,
                negod.interest AS interest,
                negod.bank_amount,
                negod.interest_days AS interest_days,
                negod.interest_pct AS interest_pct
                
			FROM `tabDoc Nego` nego
            LEFT JOIN `tabShipping Book` sb ON sb.name = nego.shipping_id
            LEFT JOIN `tabPayment Term` pt ON pt.name= sb.payment_term
			LEFT JOIN `tabCustomer` cus ON cus.name = sb.customer
			LEFT JOIN `tabNotify` noti ON noti.name = sb.notify
			LEFT JOIN `tabBank` bank ON bank.name = sb.bank
            LEFT JOIN `tabDoc Nego Details` negod ON nego.name= negod.inv_no
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
                ref.refund_amount AS bank_liab,
                refd.bank_charges AS bank_ch,
                refd.interest AS interest,
                refd.bank_amount * -1 AS bank_amount,
                refd.interest_days AS interest_days,
                refd.interest_pct AS interest_pct
			FROM `tabDoc Refund` ref
            LEFT JOIN `tabShipping Book` sb ON sb.name = ref.shipping_id
            LEFT JOIN `tabPayment Term` pt ON pt.name= sb.payment_term
			LEFT JOIN `tabCustomer` cus ON cus.name = sb.customer
			LEFT JOIN `tabNotify` noti ON noti.name =sb.notify
			LEFT JOIN `tabBank` bank ON bank.name = sb.bank
            LEFT JOIN `tabDoc Refund Details` refd ON ref.name= refd.inv_no
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
                recd.bank_liability AS bank_liab,
                recd.bank_charge + recd.foreign_charges + recd.commission + recd.postage + recd.cable_charges + recd.short_payment + recd.discrepancy_charges AS bank_ch,
                recd.interest AS interest,
                recd.bank_amount AS bank_amount,
                recd.interest_days AS interest_days,
                recd.interest_pct AS interest_pct
			FROM `tabDoc Received` rec
            LEFT JOIN `tabShipping Book` sb ON sb.name = rec.shipping_id
            LEFT JOIN `tabPayment Term` pt ON pt.name= sb.payment_term
			LEFT JOIN `tabCustomer` cus ON cus.name = sb.customer
			LEFT JOIN `tabNotify` noti ON noti.name = sb.notify
			LEFT JOIN `tabBank` bank ON bank.name = sb.bank
            LEFT JOIN `tabDoc Received Details` recd ON rec.name= recd.inv_no
			{where_clause_rec}
            
			UNION ALL
            
            SELECT 
				sb.name AS cif_id,
				intp.name,
				sb.inv_no, 
				intp.date AS date,
				"Interest" AS type,
				cus.customer, 
				noti.notify, 
				bank.bank,
				IF(pt.term_name IN ('LC', 'DA'),
					CONCAT(pt.term_name, '- ', sb.term_days),
					pt.term_name
				) AS p_term,
				sb.document,
				intp.interest AS amount,
                0 AS bank_liab,
                0 AS bank_ch,
                0 AS interest,
                0 AS bank_amount,
                0 AS interest_days,
                0 AS interest_pct
			FROM `tabInterest Paid` intp
            LEFT JOIN `tabShipping Book` sb ON sb.name = intp.shipping_id
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
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
        {"label": "Type", "fieldname": "type", "fieldtype": "Data", "width": 80},
        # {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 250},
        {"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 250},
        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 60},
        {"label": "P Term", "fieldname": "p_term", "fieldtype": "Data", "width": 95},
        {"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 125},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Float", "width": 125},
        {"label": "Bank Liab", "fieldname": "bank_liab", "fieldtype": "Float", "width": 125},
        {"label": "Bank Ch", "fieldname": "bank_ch", "fieldtype": "Float", "width": 125},
        {"label": "Interest", "fieldname": "interest", "fieldtype": "Float", "width": 125},
        {"label": "Bank Amount", "fieldname": "bank_amount", "fieldtype": "Float", "width": 125},
        {"label": "Int Days", "fieldname": "interest_days", "fieldtype": "Float", "width": 125},
        {"label": "Int %", "fieldname": "interest_pct", "fieldtype": "Float", "width": 125},
    ]

    return columns, data
