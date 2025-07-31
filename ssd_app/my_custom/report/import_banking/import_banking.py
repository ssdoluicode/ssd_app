# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
import pandas as pd

def execute(filters=None):
	# Define the report columns
	columns = [
		{"label": "LC NO", "fieldname": "lc_no", "fieldtype": "Data", "width": 85},
		{"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 85},
		{"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 120},
		{"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 70},
		{"label": "LC Open", "fieldname": "lc_o_balance", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": "LC Payment", "fieldname": "lc_p_amount", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": "Import Loan", "fieldname": "imp_loan_amount", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": "Cash Loan", "fieldname": "cash_loan", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": "Usance LC", "fieldname": "u_lc_amount", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 110},
	]

	# Raw SQL data query
	raw_data = frappe.db.sql("""
		SELECT 
			lc_o.name, 
			lc_o.lc_no,
			'' AS inv_no,
			0 AS cash_loan,
			NULL AS due_date,
			lc_o.lc_open_date AS date, 
			sup.supplier AS supplier, 
			bank.bank AS bank, 
			lc_o.currency, 
			lc_o.amount AS lc_o_amount, 
			lc_o.amount_usd AS lc_o_amount_usd, 
			lc_p.lc_p_amount, 
			imp_loan.imp_loan_amount, 
			u_lc.u_lc_amount
		FROM `tabLC Open` lc_o
		LEFT JOIN `tabSupplier` sup ON sup.name = lc_o.supplier
		LEFT JOIN `tabBank` bank ON bank.name = lc_o.bank
		LEFT JOIN (
			SELECT lc_no, SUM(amount) AS lc_p_amount 
			FROM `tabLC Payment` 
			GROUP BY lc_no
		) lc_p ON lc_p.lc_no = lc_o.name
		LEFT JOIN (
			SELECT lc_no, SUM(loan_amount) AS imp_loan_amount 
			FROM `tabImport Loan` 
			GROUP BY lc_no
		) imp_loan ON imp_loan.lc_no = lc_o.name
		LEFT JOIN (
			SELECT lc_no, SUM(usance_lc_amount) AS u_lc_amount 
			FROM `tabUsance LC` 
			GROUP BY lc_no
		) u_lc ON u_lc.lc_no = lc_o.name
	""", as_dict=True)

	# Convert to plain Python dicts from frappe._dict
	data_dicts = [dict(row) for row in raw_data]

	# Convert to Pandas DataFrame
	df = pd.DataFrame(data_dicts)

	# Handle missing numeric fields
	numeric_columns = ['lc_o_amount', 'lc_p_amount', 'imp_loan_amount', 'u_lc_amount', 'cash_loan']
	for col in numeric_columns:
		if col in df.columns:
			df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

	# Handle date columns
	if 'date' in df.columns:
		df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date

	if 'due_date' in df.columns:
		df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce').dt.date

	# Business logic: e.g. Calculate outstanding LC balance
	if all(col in df.columns for col in ['lc_o_amount', 'lc_p_amount']):
		df['lc_o_balance'] = df['lc_o_amount'] - df['lc_p_amount']- df['imp_loan_amount']- df['u_lc_amount']

	# You can optionally return 'lc_balance' if you want to include it
	# To include it, add to columns list too

	# Final output: list of dicts
	data = df.to_dict("records")

	return columns, data
