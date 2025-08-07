# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import date, timedelta

def execute(filters=None):
	columns = get_columns()
	data = get_lc_combined_data()
	return columns, data

def get_columns():
	return [
		{"label": "LC No", "fieldname": "lc_no", "fieldtype": "Data", "width": 110},
		{"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 85},
		{"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 280},
		{"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 70},
		{"label": "DocType", "fieldname": "dc_name", "fieldtype": "Data", "width": 70},#
		{"label": "LC Open", "fieldname": "lc_o_amount", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": "Import Loan", "fieldname": "imp_loan_amount", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": "Usance LC", "fieldname": "u_lc_amount", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": "Cash Loan", "fieldname": "cash_loan", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 110},
	]

def get_lc_combined_data():
	query = """
		SELECT 
			lc_o.name, 
			lc_o.lc_no,
			'' AS inv_no,
			lc_o.lc_open_date AS date, 
			sup.supplier AS supplier, 
			bank.bank AS bank,
			CASE 
				WHEN lc_o.lc_type = 'LC at Sight' THEN 's_lc_o' 
				ELSE 'u_lc_o' 
			END AS dc_name,
			lc_o.currency, 
			IF(
				lc_o.amount - IFNULL(lc_p.lc_p_amount, 0) - IFNULL(imp_loan.imp_loan_amount, 0) - IFNULL(u_lc.u_lc_amount, 0) < lc_o.amount * lc_o.tolerance / 100,
				0,
				lc_o.amount - IFNULL(lc_p.lc_p_amount, 0) - IFNULL(imp_loan.imp_loan_amount, 0) - IFNULL(u_lc.u_lc_amount, 0)
			) AS lc_o_amount,
			0 AS amount_usd, 
			0 AS imp_loan_amount,
			0 AS u_lc_amount,
			0 AS cash_loan,
			NULL AS due_date
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

		UNION ALL

		SELECT 
			imp_l.name, 
			lc_o.lc_no,
			imp_l.inv_no,
			imp_l.loan_date AS date, 
			sup.supplier AS supplier, 
			bank.bank AS bank,
			'imp_l' AS dc_name,
			lc_o.currency, 
			0 AS lc_o_amount,
			0 AS amount_usd, 
			IFNULL(imp_l.loan_amount - IFNULL(imp_l_p.imp_l_p_amount, 0), 0) AS imp_loan_amount,
			0 AS u_lc_amount,
			0 AS cash_loan,
			imp_l.due_date
		FROM `tabImport Loan` imp_l
		LEFT JOIN `tabLC Open` lc_o ON imp_l.lc_no = lc_o.name
		LEFT JOIN `tabSupplier` sup ON sup.name = lc_o.supplier
		LEFT JOIN `tabBank` bank ON bank.name = lc_o.bank
		LEFT JOIN (
			SELECT inv_no, SUM(amount) AS imp_l_p_amount
			FROM `tabImport Loan Payment` 
			GROUP BY inv_no
		) imp_l_p ON imp_l_p.inv_no = imp_l.name

		UNION ALL

		SELECT 
			u_lc.name, 
			lc_o.lc_no,
			u_lc.inv_no,
			u_lc.usance_lc_date AS date, 
			sup.supplier AS supplier, 
			bank.bank AS bank,
			'u_lc' AS dc_name,
			lc_o.currency, 
			0 AS lc_o_amount,
			0 AS amount_usd, 
			0 AS imp_loan_amount,
			IFNULL(u_lc.usance_lc_amount - IFNULL(u_lc_p.u_lc_p_amount, 0), 0) AS u_lc_amount,
			0 AS cash_loan,
			u_lc.due_date
		FROM `tabUsance LC` u_lc
		LEFT JOIN `tabLC Open` lc_o ON u_lc.lc_no = lc_o.name
		LEFT JOIN `tabSupplier` sup ON sup.name = lc_o.supplier
		LEFT JOIN `tabBank` bank ON bank.name = lc_o.bank
		LEFT JOIN (
			SELECT inv_no, SUM(amount) AS u_lc_p_amount
			FROM `tabUsance LC Payment` 
			GROUP BY inv_no
		) u_lc_p ON u_lc_p.inv_no = u_lc.name

		UNION ALL

		SELECT 
			c_loan.name, 
			c_loan.cash_loan_no AS lc_no,
			"" AS inv_no,
			c_loan.cash_loan_date AS date, 
			"" AS supplier, 
			bank.bank AS bank,
			'c_loan' AS dc_name,
			c_loan.currency, 
			0 AS lc_o_amount,
			0 AS amount_usd, 
			0 AS imp_loan_amount,
			0 AS u_lc_amount,
			IFNULL(c_loan.cash_loan_amount-IFNULL(c_loan_p.c_loan_p_amount,0), 0) AS cash_loan,
			c_loan.due_date
		FROM `tabCash Loan` c_loan
		LEFT JOIN `tabBank` bank ON bank.name = c_loan.bank
		LEFT JOIN (
			SELECT cash_loan_no, SUM(amount) AS c_loan_p_amount
			FROM `tabCash Loan Payment` 
			GROUP BY cash_loan_no
		) c_loan_p ON c_loan_p.cash_loan_no = c_loan.name;
	"""
	return frappe.db.sql(query, as_dict=True)



@frappe.whitelist()
def get_import_banking_flow(lc_no, inv_no, dc_name):
	bank = "SBI"
	customer = "SSD"

	# Table headers
	dc_labels = {
		"u_lc_o": ("Open LC", "Usance LC"),
		"s_lc_o": ("Open LC", "Import Loan"),
		"imp_l": ("Import Loan", "Payment"),
		"u_lc": ("Usance LC", "Payment"),
		"c_loan": ("Cash Loan", "Payment")
	}
	label_1, label_2 = dc_labels.get(dc_name, ("", "Payment"))

	# Get relevant records
	entries = get_entries(dc_name, lc_no)
	if entries == "Error":
		return "<p>Error: Invalid dc_name provided.</p>"

	# Generate rows
	rows_html, col_1, col_2 = build_rows(entries, dc_name)

	buttons_html= build_buttons(dc_name, lc_no, col_1, col_2)

	# Final HTML output
	return build_html(customer, bank, label_1, label_2, rows_html, buttons_html)


def get_entries(dc_name, lc_no):
	if dc_name == "s_lc_o":
		return frappe.db.sql("""
			SELECT name, 'LC Open' AS Type, lc_open_date AS Date, amount, '' AS Inv_no, currency 
			FROM `tabLC Open` WHERE name=%s
			UNION ALL
			SELECT name, 'LC Paid', date, amount, inv_no, currency 
			FROM `tabLC Payment` WHERE lc_no=%s
			UNION ALL
			SELECT name, 'Import Loan', loan_date, loan_amount, inv_no, currency 
			FROM `tabImport Loan` WHERE lc_no=%s
			UNION ALL
			SELECT imp_l_p.name, 'Imp Loan Payment', imp_l_p.payment_date, imp_l_p.amount, imp_l.inv_no, imp_l.currency 
			FROM `tabImport Loan Payment` imp_l_p 
			LEFT JOIN `tabImport Loan` imp_l ON imp_l.name = imp_l_p.inv_no 
			WHERE imp_l.lc_no=%s
		""", (lc_no, lc_no, lc_no, lc_no), as_dict=1)

	elif dc_name == "u_lc_o":
		return frappe.db.sql("""
			SELECT name, 'LC Open' AS Type, lc_open_date AS Date, amount, '' AS Inv_no, currency 
			FROM `tabLC Open` WHERE name=%s
			UNION ALL
			SELECT name, 'LC Paid', date, amount, inv_no, currency 
			FROM `tabLC Payment` WHERE lc_no=%s
			UNION ALL
			SELECT name, 'Usance LC', usance_lc_date, usance_lc_amount AS amount, inv_no, currency 
			FROM `tabUsance LC` WHERE lc_no=%s
			UNION ALL
			SELECT u_lc_p.name, 'Usance LC Payment', u_lc_p.payment_date, u_lc_p.amount, u_lc_p.inv_no, u_lc_p.currency 
			FROM `tabUsance LC Payment` u_lc_p 
			LEFT JOIN `tabUsance LC` u_lc ON u_lc.name = u_lc_p.inv_no 
			WHERE u_lc.lc_no=%s
		""", (lc_no, lc_no, lc_no, lc_no), as_dict=1)

	elif dc_name == "c_loan":
		return frappe.db.sql("""
			SELECT name, 'Cash Loan' AS Type, cash_loan_date AS Date, cash_loan_amount AS amount, '' AS Inv_no, currency 
			FROM `tabCash Loan` WHERE name=%s
			UNION ALL
			SELECT c_l_p.name, 'Cash Loan Paid', c_l_p.payment_date , c_l_p.amount, c_l.cash_loan_no AS Inv_no, c_l_p.currency 
			FROM `tabCash Loan Payment` c_l_p LEFT JOIN `tabCash Loan` c_l ON c_l_p.cash_loan_no= c_l.name WHERE c_l_p.cash_loan_no=%s
		""", (lc_no, lc_no), as_dict=1)

	elif dc_name == "imp_l":
		return frappe.db.sql("""
			SELECT name, 'Import Loan' AS Type, loan_date AS Date, loan_amount AS amount, inv_no AS Inv_no, currency 
			FROM `tabImport Loan` WHERE name=%s
			UNION ALL
			SELECT imp_l_p.name, 'Imp Loan Payment', imp_l_p.payment_date, imp_l_p.amount, imp_l.inv_no, imp_l.currency 
			FROM `tabImport Loan Payment` imp_l_p 
			LEFT JOIN `tabImport Loan` imp_l ON imp_l.name = imp_l_p.inv_no 
			WHERE imp_l_p.inv_no=%s
		""", (lc_no, lc_no), as_dict=1)
	
	elif dc_name == "u_lc":
		return frappe.db.sql("""
			SELECT name, 'Usance LC' AS Type, usance_lc_date AS Date, usance_lc_amount AS amount, inv_no AS Inv_no, currency 
			FROM `tabUsance LC` WHERE name=%s
			UNION ALL
			SELECT u_lc_p.name, 'Usance LC Payment', u_lc_p.payment_date , u_lc_p.amount, u_lc.inv_no, u_lc_p.currency 
			FROM `tabUsance LC Payment` u_lc_p 
			LEFT JOIN `tabUsance LC` u_lc ON u_lc.name = u_lc_p.inv_no 
			WHERE u_lc_p.inv_no=%s
		""", (lc_no, lc_no), as_dict=1)

	return "Error"


def build_rows(entries, dc_name):
	col_1, col_2 = 0, 0
	rows = []

	for e in entries:
		type_ = e["Type"]
		amount = e["amount"] or 0

		# Column calculations
		if type_ == "LC Open":
			col_1 += amount
		elif type_ == "LC Paid":
			col_1 -= amount
		elif type_ == "Cash Loan":
			col_1 += amount
		elif type_ == "Cash Loan Paid":
			col_1 -= amount
			col_2 += amount
		elif dc_name == "s_lc_o" and type_ == "Import Loan":
			col_1 -= amount
			col_2 += amount
		elif dc_name == "u_lc_o" and type_ == "Usance LC":
			col_1 -= amount
			col_2 += amount
		elif dc_name == "s_lc_o" and type_ == "Imp Loan Payment":
			col_2 -= amount
		elif dc_name == "u_lc_o" and type_ == "Usance LC Payment":
			col_2 -= amount
		elif dc_name == "imp_l" and type_ == "Import Loan":
			col_1 += amount
		elif dc_name == "imp_l" and type_ == "Imp Loan Payment":
			col_1 -= amount
			col_2 += amount
		elif dc_name == "u_lc" and type_ == "Usance LC":
			col_1 += amount
		elif dc_name == "u_lc" and type_ == "Usance LC Payment":
			col_1 -= amount
			col_2 += amount
			

		# Row HTML
		rows.append(f"""
			<tr>
				<td>{e['Date']}</td>
				<td>{e['Inv_no']}</td>
				<td style="text-align:right;">{amount:,.2f}</td>
				<td>{type_}</td>
				<td style="text-align:right;">{col_1:,.2f}</td>
				<td style="text-align:right;">{col_2:,.2f}</td>
				<td style="text-align:right;">-</td>
			</tr>
		""")

	return rows, col_1, col_2

def build_buttons(dc_name, lc_no, col_1, col_2):
	today_str = date.today().strftime("%Y-%m-%d")
	buttons_html = ""
	if dc_name =="s_lc_o":
		if col_1 > 0:
			buttons_html += f"""
			<a href="#" onclick="frappe.new_doc('Import Loan', {{ lc_no: '{lc_no}', loan_date:'{today_str}', loan_amount: {col_1} }}); return false;" class="btn btn-primary btn-sm" style="margin-left:8px;background-color:blue;">Import Loan</a>
			<a href="#" onclick="frappe.new_doc('LC Payment', {{ lc_no: '{lc_no}', loan_date:'{today_str}', amount: {col_1} }}); return false;" class="btn btn-primary btn-sm" style="margin-left:8px;background-color:green;">LC Payment</a>
			"""
	if dc_name =="u_lc_o":
		if col_1 > 0:
			buttons_html += f"""
			<a href="#" onclick="frappe.new_doc('Usance LC', {{ lc_no: '{lc_no}', usance_lc_date:'{today_str}', usance_lc_amount: {col_1} }}); return false;" class="btn btn-primary btn-sm" style="margin-left:8px;background-color:blue;">Usance LC</a>
			<a href="#" onclick="frappe.new_doc('LC Payment', {{ lc_no: '{lc_no}', loan_date:'{today_str}', amount: {col_1} }}); return false;" class="btn btn-primary btn-sm" style="margin-left:8px;background-color:green;">LC Payment</a>
			"""
			# if nego_amt > 0:
	# 	buttons_html += f"""
	# 	<a href="#" onclick="frappe.new_doc('Doc Refund', {{ inv_no: '{inv_name}', refund_date:'{today_str}', refund_amount:'{nego_amt}' }}); return false;" class="btn btn-danger btn-sm" style="margin-left:8px;background-color:red;">Refund</a>"""
	# if (doc_amount - received) > 0:
	# 	buttons_html += f"""
	# 	<a href="#" onclick="frappe.new_doc('Doc Received', {{ inv_no: '{inv_name}', received_date:'{today_str}', received:'{doc_amount - received}' }}); return false;" class="btn btn-success btn-sm" style="margin-left:8px;background-color:green;">Received</a>"""

	return buttons_html


def build_html(customer, bank, label_1, label_2, rows_html, buttons_html):
	return f"""
	<div style="margin-bottom: 12px; background-color: #f9f9f9; padding: 8px 12px; border-radius: 6px;
	box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
		<table style="width:100%; font-size:13px;">
			<tr>
				<td><b>Supplier: ##########</b></td>
				
			</tr>
			<tr>
				<td><b>Bank:</b> {bank}</td>
				
			</tr>
		</table>
	</div>

	<table class="table table-bordered" style="font-size:14px; border:1px solid #ddd;">
		<thead style="background-color: #f1f1f1;">
			<tr>
				<th style="width:14%; text-align:center;">Date</th>
				<th style="width:16%; text-align:center;">Inv No</th>
				<th style="width:15%; text-align:center;">Amount</th>
				<th style="width:20%; text-align:center;">Details</th>
				<th style="width:15%; text-align:center;">{label_1}</th>
				<th style="width:15%; text-align:center;">{label_2}</th>
				<th style="width:5%; text-align:center;">Note</th>
			</tr>
		</thead>
		<tbody>
			{''.join(rows_html)}
		</tbody>
	</table>
	{buttons_html}
	<div style="text-align:right; margin-top:12px; padding:8px; border-top:1px solid #eee;"></div>
	"""

