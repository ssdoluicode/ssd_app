# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = [
		{"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 150},
		{"label": "Received", "fieldname": "received", "fieldtype": "Float", "width": 110},
		{"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 90}
	]

	data= frappe.db.sql(f"""
		SELECT cif.inv_no AS inv_no, cus.customer AS customer, bank.bank AS bank, dr.received AS received FROM `tabDoc Received`  dr
		LEFT JOIN `tabCIF Sheet` cif ON cif.name= dr.inv_no
		LEFT JOIN `tabBank` bank ON bank.name= dr.bank
		LEFT JOIN `tabCustomer` cus ON cus.name= dr.customer
		WHERE received_date= '2025-10-28'
		""", as_dict=1)
	return columns, data
