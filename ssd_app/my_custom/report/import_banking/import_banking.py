# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):

	columns = [
		{"label": "LC NO", "fieldname": "lc_no", "fieldtype": "Data", "width": 85},
		{"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 120},
		{"label": "Bank","fieldname": "bank","fieldtype": "Data", "width": 70},
		{"label": "LC Open", "fieldname": "lc_o_amount", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": "LC Payment", "fieldname": "lc_p_amount", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": "Import Loan", "fieldname": "imp_loan_amount", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": "Usance LC", "fieldname": "u_lc_amount", "fieldtype": "Currency", "options": "currency", "width": 130}
	]

	data = frappe.db.sql(f"""
		SELECT 
	lc_o.name, 
    lc_o.lc_no, 
    lc_o.lc_open_date AS date, 
    sup.supplier AS supplier, bank.bank AS bank, lc_o.currency, lc_o.amount AS lc_o_amount, 
	lc_o.amount_usd AS lc_o_amount_usd, lc_p.lc_p_amount, imp_loan.imp_loan_amount, u_lc.u_lc_amount
FROM `tabLC Open` lc_o
LEFT JOIN `tabSupplier` sup ON sup.name = lc_o.supplier
LEFT JOIN `tabBank` bank on bank.name= lc_o.bank
LEFT JOIN (SELECT lc_no,SUM(amount) AS lc_p_amount FROM `tabLC Payment` GROUP BY lc_no) lc_p ON lc_p.lc_no= lc_o.name
LEFT JOIN (SELECT lc_no,SUM(loan_amount) AS imp_loan_amount FROM `tabImport Loan` GROUP BY lc_no) imp_loan ON imp_loan.lc_no= lc_o.name
LEFT JOIN (SELECT lc_no,SUM(usance_lc_amount) AS u_lc_amount FROM `tabUsance LC` GROUP BY lc_no) u_lc ON u_lc.lc_no= lc_o.name
	""", as_dict=1)
	return columns, data
