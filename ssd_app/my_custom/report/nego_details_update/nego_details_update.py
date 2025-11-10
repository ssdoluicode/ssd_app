# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	data = frappe.db.sql(f"""
	SELECT inv_no, customer from `tabDoc Nego`
		
	""", as_dict=1)
	columns = [
		{"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 85},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 85},
	]
	return columns, data
