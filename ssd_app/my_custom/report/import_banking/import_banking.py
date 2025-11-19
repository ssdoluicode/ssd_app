# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from datetime import date, timedelta
from frappe.utils import formatdate, fmt_money


def execute(filters=None):
	columns = get_columns()
	data = get_lc_combined_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "LC No", "fieldname": "lc_no", "fieldtype": "Data", "width": 110},
		{"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 85},
		{"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 280},
		{"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 70},
		# {"label": "DocType", "fieldname": "dc_name", "fieldtype": "Data", "width": 70},
		{"label": "LC Open", "fieldname": "lc_o_amount", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": "Import Loan", "fieldname": "imp_loan_amount", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": "Usance LC", "fieldname": "u_lc_amount", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": "Cash Loan", "fieldname": "cash_loan", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 110},
		{"label": "Note", "fieldname": "note", "fieldtype": "Data", "width": 110}
	]


def get_conditions(based_on):
	"""Returns SQL WHERE conditions for each LC type depending on 'based_on' filter."""
	conditions = {
		"lc_o": "",
		"imp_loan": "",
		"u_lc": "",
		"cash_loan": ""
	}

	if based_on == "Current Position":
		conditions.update({
			"lc_o": "AND (lc_o.amount - IFNULL(lc_p.lc_p_amount, 0) - IFNULL(imp_loan.imp_loan_amount, 0) - IFNULL(u_lc.u_lc_amount, 0) != 0)",
			"imp_loan": "AND (IFNULL(imp_l.loan_amount - IFNULL(imp_l_p.imp_l_p_amount, 0), 0) != 0)",
			"u_lc": "AND (IFNULL(u_lc.usance_lc_amount - IFNULL(u_lc_p.u_lc_p_amount, 0), 0) != 0)",
			"cash_loan": "AND (IFNULL(c_loan.cash_loan_amount - IFNULL(c_loan_p.c_loan_p_amount, 0), 0) != 0)"
		})

	elif based_on == "LC Open":
		conditions.update({"lc_o": "AND (lc_o.amount - IFNULL(lc_p.lc_p_amount, 0) - IFNULL(imp_loan.imp_loan_amount, 0) - IFNULL(u_lc.u_lc_amount, 0) != 0)",
						   "imp_loan": "AND 1=0", "u_lc": "AND 1=0", "cash_loan": "AND 1=0"})

	elif based_on == "Usance LC":
		conditions.update({"lc_o": "AND 1=0", "imp_loan": "AND 1=0",
						   "u_lc": "AND (IFNULL(u_lc.usance_lc_amount - IFNULL(u_lc_p.u_lc_p_amount, 0), 0) != 0)",
						   "cash_loan": "AND 1=0"})

	elif based_on == "Import Loan":
		conditions.update({"lc_o": "AND 1=0",
						   "imp_loan": "AND (IFNULL(imp_l.loan_amount - IFNULL(imp_l_p.imp_l_p_amount, 0), 0) != 0)",
						   "u_lc": "AND 1=0", "cash_loan": "AND 1=0"})

	elif based_on == "Cash Loan":
		conditions.update({"lc_o": "AND 1=0", "imp_loan": "AND 1=0", "u_lc": "AND 1=0",
						   "cash_loan": "AND (IFNULL(c_loan.cash_loan_amount - IFNULL(c_loan_p.c_loan_p_amount, 0), 0) != 0)"})

	return conditions


def get_lc_combined_data(filters):
	as_on = filters.as_on
	based_on = filters.based_on or ""
	conds = get_conditions(based_on)

	# Full query with placeholders for parameters
	query = f"""
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
			lc_o.amount - IFNULL(lc_p.lc_p_amount, 0) AS lc_o_amount,
			0 AS amount_usd, 
			0 AS imp_loan_amount,
			0 AS u_lc_amount,
			0 AS cash_loan,
			NULL AS due_date,
			1 as due_date_confirm, 
			100 AS days_to_due,
			lc_o.note
		FROM `tabLC Open` lc_o
		LEFT JOIN `tabSupplier` sup ON sup.name = lc_o.supplier
		LEFT JOIN `tabBank` bank ON bank.name = lc_o.bank
		LEFT JOIN (
			SELECT lc_no, SUM(amount) AS lc_p_amount 
			FROM `tabLC Payment` 
			WHERE date <= %(as_on)s
			GROUP BY lc_no
		) lc_p ON lc_p.lc_no = lc_o.name
		LEFT JOIN (
			SELECT lc_no, SUM(loan_amount) AS imp_loan_amount 
			FROM `tabImport Loan`
			WHERE loan_date <= %(as_on)s
			GROUP BY lc_no
		) imp_loan ON imp_loan.lc_no = lc_o.name
		LEFT JOIN (
			SELECT lc_no, SUM(usance_lc_amount) AS u_lc_amount 
			FROM `tabUsance LC`
			WHERE usance_lc_date <= %(as_on)s
			GROUP BY lc_no
		) u_lc ON u_lc.lc_no = lc_o.name
		WHERE lc_o.lc_open_date <= %(as_on)s {conds['lc_o']}

		UNION ALL
		-- Import Loan
		SELECT 
			imp_l.name, 
			"imp l" AS lc_no,
			imp_l.inv_no,
			imp_l.loan_date AS date, 
			sup.supplier AS supplier, 
			bank.bank AS bank,
			'imp_l' AS dc_name,
			imp_l.currency, 
			0 AS lc_o_amount,
			0 AS amount_usd, 
			IFNULL(imp_l.loan_amount - IFNULL(imp_l_p.imp_l_p_amount, 0), 0) AS imp_loan_amount,
			0 AS u_lc_amount,
			0 AS cash_loan,
			imp_l.due_date,
			imp_l.due_date_confirm AS due_date_confirm,
			CASE WHEN imp_l.due_date IS NOT NULL THEN DATEDIFF(imp_l.due_date, CURDATE()) END AS days_to_due,
			imp_l.note
		FROM `tabImport Loan` imp_l
		LEFT JOIN `tabSupplier` sup ON sup.name = imp_l.supplier
		LEFT JOIN `tabBank` bank ON bank.name = imp_l.bank
		LEFT JOIN (
			SELECT inv_no, SUM(amount) AS imp_l_p_amount
			FROM `tabImport Loan Payment` 
			WHERE payment_date <= %(as_on)s
			GROUP BY inv_no
		) imp_l_p ON imp_l_p.inv_no = imp_l.name
		WHERE imp_l.loan_date <= %(as_on)s {conds['imp_loan']}

		UNION ALL
		-- Usance LC
		SELECT 
			u_lc.name, 
			"u_lc" AS lc_no,
			u_lc.inv_no,
			u_lc.usance_lc_date AS date, 
			sup.supplier AS supplier, 
			bank.bank AS bank,
			'u_lc' AS dc_name,
			u_lc.currency, 
			0 AS lc_o_amount,
			0 AS amount_usd, 
			0 AS imp_loan_amount,
			IFNULL(u_lc.usance_lc_amount - IFNULL(u_lc_p.u_lc_p_amount, 0), 0) AS u_lc_amount,
			0 AS cash_loan,
			u_lc.due_date,
			u_lc.due_date_confirm AS due_date_confirm,
			CASE WHEN u_lc.due_date IS NOT NULL THEN DATEDIFF(u_lc.due_date, CURDATE()) END AS days_to_due,
			u_lc.note
		FROM `tabUsance LC` u_lc
		LEFT JOIN `tabSupplier` sup ON sup.name = u_lc.supplier
		LEFT JOIN `tabBank` bank ON bank.name = u_lc.bank
		LEFT JOIN (
			SELECT inv_no, SUM(amount) AS u_lc_p_amount
			FROM `tabUsance LC Payment` 
			WHERE payment_date <= %(as_on)s
			GROUP BY inv_no
		) u_lc_p ON u_lc_p.inv_no = u_lc.name
		WHERE u_lc.usance_lc_date <= %(as_on)s {conds['u_lc']}

		UNION ALL
		-- Cash Loan
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
			IFNULL(c_loan.cash_loan_amount - IFNULL(c_loan_p.c_loan_p_amount, 0), 0) AS cash_loan,
			c_loan.due_date,
			c_loan.due_date_confirm AS due_date_confirm,
			CASE WHEN c_loan.due_date IS NOT NULL THEN DATEDIFF(c_loan.due_date, CURDATE()) END AS days_to_due,
			c_loan.note
		FROM `tabCash Loan` c_loan
		LEFT JOIN `tabBank` bank ON bank.name = c_loan.bank
		LEFT JOIN (
			SELECT cash_loan_no, SUM(amount) AS c_loan_p_amount
			FROM `tabCash Loan Payment` 
			WHERE payment_date <= %(as_on)s
			GROUP BY cash_loan_no
		) c_loan_p ON c_loan_p.cash_loan_no = c_loan.name
		WHERE c_loan.cash_loan_date <= %(as_on)s {conds['cash_loan']}
	"""

	# Execute with parameter binding
	return frappe.db.sql(query, {
		"as_on": as_on
	}, as_dict=True)




@frappe.whitelist()
def get_import_banking_flow(name, dc_name, supplier_name, bank_name):

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
	entries = get_entries(dc_name, name)
	if entries == "Error":
		return "<p>Error: Invalid dc_name provided.</p>"
	else:
		entries = sorted(entries, key=lambda x: x.get("Date") or "")

	# Generate rows
	rows_html, col_1, col_2 = build_rows(entries, dc_name)

	buttons_html= build_buttons(dc_name, name, col_1, col_2)

	# Final HTML output
	return build_html(supplier_name, bank_name, dc_name, label_1, label_2, rows_html, buttons_html)


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
			SELECT name, 'U LC', usance_lc_date, usance_lc_amount AS amount, inv_no, currency 
			FROM `tabUsance LC` WHERE lc_no=%s
			UNION ALL
			SELECT u_lc_p.name, 'U LC Payment', u_lc_p.payment_date, u_lc_p.amount, u_lc_p.inv_no, u_lc_p.currency 
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
			SELECT name, 'U LC' AS Type, usance_lc_date AS Date, usance_lc_amount AS amount, inv_no AS Inv_no, currency 
			FROM `tabUsance LC` WHERE name=%s
			UNION ALL
			SELECT u_lc_p.name, 'U LC Payment', u_lc_p.payment_date , u_lc_p.amount, u_lc.inv_no, u_lc_p.currency 
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
		elif dc_name == "u_lc_o" and type_ == "U LC":
			col_1 -= amount
			col_2 += amount
		elif dc_name == "s_lc_o" and type_ == "Imp Loan Payment":
			col_2 -= amount
		elif dc_name == "u_lc_o" and type_ == "U LC Payment":
			col_2 -= amount
		elif dc_name == "imp_l" and type_ == "Import Loan":
			col_1 += amount
		elif dc_name == "imp_l" and type_ == "Imp Loan Payment":
			col_1 -= amount
			col_2 += amount
		elif dc_name == "u_lc" and type_ == "U LC":
			col_1 += amount
		elif dc_name == "u_lc" and type_ == "U LC Payment":
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

    def quick_btn(label, doctype, **kwargs):
        # Convert kwargs to JS object string for frappe.new_doc
        params_js = "{" + ", ".join([f'"{k}": "{v}"' for k, v in kwargs.items()]) + "}"
        return f"""
        <button class="btn btn-primary btn-sm"
            style="margin:4px;"
            onclick='frappe.new_doc("{doctype}", {params_js})'>
            {label}
        </button>
        """

    if dc_name == "s_lc_o" and col_1 > 0:
        buttons_html += quick_btn("Import Loan", "Import Loan",
                                  lc_no=lc_no, loan_date=today_str, loan_amount=col_1)
        buttons_html += quick_btn("LC Payment", "LC Payment",
                                  lc_no=lc_no, date=today_str, amount=col_1)

    elif dc_name == "u_lc_o" and col_1 > 0:
        buttons_html += quick_btn("U LC", "Usance LC",
                                  lc_no=lc_no, usance_lc_date=today_str, usance_lc_amount=col_1)
        buttons_html += quick_btn("LC Payment", "LC Payment",
                                  lc_no=lc_no, date=today_str, amount=col_1)

    elif dc_name == "imp_l" and col_1 > 0:
        buttons_html += quick_btn("Imp Loan Payment", "Import Loan Payment",
                                  inv_no=lc_no, payment_date=today_str, amount=col_1)

    elif dc_name == "u_lc" and col_1 > 0:
        buttons_html += quick_btn("U LC Payment", "Usance LC Payment",
                                  inv_no=lc_no, payment_date=today_str, amount=col_1)

    elif dc_name == "c_loan" and col_1 > 0:
        buttons_html += quick_btn("Cash Loan Payment", "Cash Loan Payment",
                                  cash_loan_no=lc_no, payment_date=today_str, amount=col_1)

    # return f'<div id="lc-buttons" style="margin-top: 12px; right: 10px; float:right;">{buttons_html}</div>'
    return f'<div id="lc-buttons" style="margin-top:30px; float:right;">{buttons_html}</div>'



def build_html(supplier_name, bank_name, term, label_1, label_2, rows_html, buttons_html):
	return f"""
	<div style="margin-bottom: 12px; background-color: #f9f9f9; padding: 8px 12px; border-radius: 6px;
	box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
		<table style="width:100%; font-size:13px;">
			<tr>
				<td><b>Supplier: {supplier_name}</b></td>
				
			</tr>
			<tr>
				<td><b>Term:</b> {term}</td>
				
			</tr>
			<tr>
				<td><b>Bank:</b> {bank_name}</td>
				
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

