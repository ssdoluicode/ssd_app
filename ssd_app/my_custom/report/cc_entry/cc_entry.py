# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}
	status_filter = filters.get("status", "Pending")   # default Pending   

	where_clause=""
	if status_filter == "Pending":
		where_clause = " AND ccr.cc_received_details != 1"
	
	elif status_filter == "Updated":
		where_clause = " AND ccr.cc_received_details = 1"

	query= f"""
		SELECT ccr.name, cus.customer, ccr.date, ccr.currency, ccr.amount, ccr.cc_received_details AS details FROM `tabCC Received` ccr
		LEFT JOIN `tabCustomer` cus on cus.name= ccr.customer
		WHERE ccr.entry_type= 'Bank Entry' {where_clause}
		ORDER BY ccr.date
	"""
	
	data = frappe.db.sql(query, as_dict=1)
	columns =  [
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 250},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": "Currency", "fieldname": "currency", "fieldtype": "Data", "width": 110},
		{"label": "Amount", "fieldname": "amount", "fieldtype": "Float", "width": 150},
		{"label": "Action", "fieldname": "action", "fieldtype": "Data", "width": 150},
		
	]
	return columns, data
