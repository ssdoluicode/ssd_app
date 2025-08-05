# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
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
	bank= "SBI"
	customer= "SSD"
	dc_name_labels_1 = {"u_lc_o": "Open LC","s_lc_o": "Open LC","imp_loan": "Import Loan", "u_lc": "Usance LC",
					 "c_loan": "Cash Loan"}

	dc_name_labels_2 = {"u_lc_o": "Usance LC","s_lc_o": "Import Loan"}

	table_head_label_1 = dc_name_labels_1.get(dc_name, "")
	table_head_label_2 = dc_name_labels_2.get(dc_name, "Payment")

	if dc_name== "s_lc_o":
		entries = frappe.db.sql("""
		SELECT name, 'LC Open' AS Type, lc_open_date AS Date, amount AS Amount,"" AS Inv_no, currency AS Curr FROM `tabLC Open` WHERE name=%s
		UNION ALL
		SELECT name, 'LC Paid', date, amount, inv_no, currency FROM `tabLC Payment` WHERE lc_no=%s
		UNION ALL
		SELECT name, 'Import Loan', loan_date, loan_amount, inv_no, currency FROM `tabImport Loan` WHERE lc_no=%s
		UNION ALL
		select imp_l_p.name,"Imp Loan Payment",imp_l_p.payment_date, imp_l_p.amount, imp_l.inv_no, imp_l.currency 
						  from `tabImport Loan Payment` imp_l_p left join  `tabImport Loan` imp_l on imp_l.name= imp_l_p.inv_no WHERE imp_l.lc_no=%s
	""", (lc_no, lc_no, lc_no, lc_no), as_dict=1)
	
	elif dc_name== "u_lc_o":
		entries = frappe.db.sql("""
		SELECT name, 'LC Open' AS Type, lc_open_date AS Date, amount AS Amount,"" AS Inv_no, currency AS Curr FROM `tabLC Open` WHERE name=%s
		UNION ALL
		SELECT name, 'LC Paid', date, amount, inv_no, currency FROM `tabLC Payment` WHERE lc_no=%s
		UNION ALL
		SELECT name, 'Usance LC', usance_lc_date, usance_lc_amount, inv_no, currency FROM `tabUsance LC` WHERE lc_no=%s
		UNION ALL
		select u_lc_p.name,"Usance LC Payment",u_lc_p.payment_date, u_lc_p.amount, u_lc_p.inv_no, u_lc_p.currency 
						  from `tabUsance LC Payment` u_lc_p left join  `tabUsance LC` u_lc on u_lc.name= u_lc_p.inv_no WHERE u_lc.lc_no=%s
	""", (lc_no, lc_no, lc_no, lc_no), as_dict=1)
		
	elif dc_name== "c_loan":
		entries = frappe.db.sql("""
		SELECT name, 'Cash Loan' AS Type, cash_loan_date AS Date, cash_loan_amount AS Amount, "" AS Inv_no, currency AS Curr FROM `tabCash Loan` imp_l WHERE name=%s 
		UNION ALL
		SELECT name, "Cash Loan Payment", payment_date, amount, cash_loan_no, currency FROM `tabCash Loan Payment` WHERE cash_loan_no=%s

	""", (lc_no,lc_no), as_dict=1)

	else:
		entries= "Error"

	entries.sort(key=lambda x: x["Date"] or date.today())

	rows = []
	col_1=0
	col_2=0

	for entry in entries:
		if (entry['Type']== "LC Open"):
			col_1+=entry["Amount"]
		
		if (entry['Type']== "LC Paid"):
			col_1-=entry["Amount"]
		
		if (entry['Type']== "Import Loan" or entry['Type']== "Usance LC"):
			col_1-=entry["Amount"]
			col_2+=entry["Amount"]

		if (entry['Type']== "Imp Loan Payment" or entry['Type']== "Usance LC Payment"):
			col_2-=entry["Amount"]
		

		rows.append(f"""
			<tr>
			  	<td>{entry['Date']}</td>
				  <td>{entry['Inv_no']}</td>
				<td style="text-align:right;">{entry["Amount"]}</td>
				<td>{entry['Type']}</td>
				<td style="text-align:right;">{col_1}</td>
				<td style="text-align:right;">{col_2}</td>

				<td style="text-align:right;">note</td>
			</tr>
		""")


	# Build final HTML
	html = f"""
	<div style="bmargin-bottom: 12px; background-color: #f9f9f9; padding: 8px 12px;  border-radius: 6px; 
	box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
    <table style="width:100%; font-size:13px; margin-bottom:0;">
			<tr><td><b>Invoice Date:</b> </td><td><b>Customer:</b> {customer}</td><td><b>Notify:</b> </td></tr>
			<tr><td><b>Bank:</b> {bank}</td><td><b>Payment Term:</b> </td><td><b>Category:</b></td></tr>
		</table>
	</div>
	<table class="table table-bordered" style="font-size:14px; border:1px solid #ddd;">
		<thead style="background-color: #f1f1f1;">
			<tr>
				<th style="width:15%; text-align:center;">Date</th>
				<th style="width:15%; text-align:center;">Inv No</th>
				<th style="width:10%;text-align:center;">Amount</th>
				<th style="width:10%; text-align:center;">Type</th>
				<th style="width:10%;text-align:center;">{table_head_label_1}</th>
				<th style="width:10%;text-align:center;">{table_head_label_2}</th>
				<th style="width:15%;text-align:center;">Note</th>
			</tr>
		</thead>
		<tbody style="border-top:1px solid #ddd;">

			{''.join(rows)}
		</tbody>
	</table>
	<div style="text-align:right; margin-top:12px;padding:8px; border-top:1px solid #eee;">
	{entries}
	</div>
	"""
	return html

	
	
