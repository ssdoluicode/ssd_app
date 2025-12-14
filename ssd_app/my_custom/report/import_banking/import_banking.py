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
		# {"label": "LC No", "fieldname": "lc_no", "fieldtype": "Data", "width": 110},
		{"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 85},
		{"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 280},
		{"label": "Company", "fieldname": "com", "fieldtype": "Data", "width": 110},
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
			"lc_o": "AND (lco.lc_open_amount - COALESCE(lcp.lc_payment_amount, 0)) != 0",
			"imp_loan": "AND (IFNULL(imp_l.loan_amount - IFNULL(imp_l_p.imp_l_p_amount, 0), 0) != 0)",
			"u_lc": "AND (IFNULL(u_lc.usance_lc_amount - IFNULL(u_lc_p.u_lc_p_amount, 0), 0) != 0)",
			"cash_loan": "AND (IFNULL(c_loan.cash_loan_amount - IFNULL(c_loan_p.c_loan_p_amount, 0), 0) != 0)"
		})

	elif based_on == "LC Open":
		conditions.update({"lc_o": "AND (lco.lc_open_amount - COALESCE(lcp.lc_payment_amount, 0)) != 0",
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
			lco.group_id AS name,
			"" AS lc_no,
			"" AS inv_no,
			date,
			"" AS supplier,
			com.company_code AS com,
			bank.bank AS bank,
			'lc_o' AS dc_name,
			"USD" AS currency,
			(lco.lc_open_amount - COALESCE(lcp.lc_payment_amount, 0)- COALESCE(imp_ln.to_imp_ln, 0)- COALESCE(usance_lc.to_usamce_lc, 0)) AS lc_o_amount,
			0 AS imp_loan_amount,
			0 AS u_lc_amount,
			0 AS cash_loan,
			NULL AS due_date,
			1 as due_date_confirm, 
			100 AS days_to_due,
			"" AS note
		FROM
			(
				SELECT group_id, MAX(lc_open_date) AS date, company, bank, SUM(amount_usd) AS lc_open_amount
				FROM `tabLC Open`
				WHERE lc_open_date <= %(as_on)s
				GROUP BY group_id
			) lco
		LEFT JOIN
			(
				SELECT group_id, company, bank, SUM(amount_usd) AS lc_payment_amount
				FROM `tabLC Payment`
				WHERE date <= %(as_on)s
				GROUP BY group_id
			) lcp
		ON lco.group_id = lcp.group_id
		LEFT JOIN
			(
				SELECT group_id, company, bank, SUM(loan_amount_usd) AS to_imp_ln
				FROM `tabImport Loan`
				WHERE loan_date <= %(as_on)s AND from_lc_open=1
				GROUP BY group_id
			) imp_ln
		ON lco.group_id = imp_ln.group_id
		LEFT JOIN
			(
				SELECT group_id, company, bank, SUM(usance_lc_amount_usd) AS to_usamce_lc
				FROM `tabUsance LC`
				WHERE usance_lc_date <= %(as_on)s AND from_lc_open=1
				GROUP BY group_id
			) usance_lc
		ON lco.group_id = usance_lc.group_id
		LEFT JOIN `tabBank` bank ON bank.name= lco.bank
		LEFT JOIN `tabCompany` com ON com.name= lco.company
		WHERE 1=1  {conds['lc_o']}

		UNION ALL

		-- Import Loan
		SELECT 
			imp_l.name, 
			"imp l" AS lc_no,
			imp_l.inv_no,
			imp_l.loan_date AS date, 
			sup.supplier AS supplier, 
			com.company_code AS com,
			bank.bank AS bank,
			'imp_l' AS dc_name,
			imp_l.currency, 
			0 AS lc_o_amount,
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
		LEFT JOIN `tabCompany` com ON com.name= imp_l.company
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
			com.company_code AS com,
			bank.bank AS bank,
			'u_lc' AS dc_name,
			u_lc.currency, 
			0 AS lc_o_amount,
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
		LEFT JOIN `tabCompany` com ON com.name= u_lc.company
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
			"" AS lc_no,
			c_loan.cash_loan_no AS inv_no,
			c_loan.cash_loan_date AS date, 
			"" AS supplier, 
			com.company_code AS com,
			bank.bank AS bank,
			'c_loan' AS dc_name,
			c_loan.currency, 
			0 AS lc_o_amount, 
			0 AS imp_loan_amount,
			0 AS u_lc_amount,
			IFNULL(c_loan.cash_loan_amount - IFNULL(c_loan_p.c_loan_p_amount, 0), 0) AS cash_loan,
			c_loan.due_date,
			c_loan.due_date_confirm AS due_date_confirm,
			CASE WHEN c_loan.due_date IS NOT NULL THEN DATEDIFF(c_loan.due_date, CURDATE()) END AS days_to_due,
			c_loan.note
		FROM `tabCash Loan` c_loan
		LEFT JOIN `tabBank` bank ON bank.name = c_loan.bank
		LEFT JOIN `tabCompany` com ON com.name= c_loan.company
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

	# Get relevant records
	entries = get_entries(dc_name, name)
	if entries == "Error":
		return "<p>Error: Invalid dc_name provided.</p>"
	else:
		entries = sorted(entries, key=lambda x: x.get("Date") or "")

	# Generate rows
	rows_html, col_1 = build_rows(entries)

	buttons_html= build_buttons(dc_name, name, col_1)

	# Final HTML output
	return build_html(supplier_name, bank_name, dc_name, rows_html, buttons_html)


def get_entries(dc_name, name):
	
	if dc_name == "lc_o":
		
		return frappe.db.sql("""
			SELECT
				lc_o.group_id AS name,
				'LC Open' AS Type,
				'rec' AS t_type,
				lc_o.lc_open_date AS Date,
				lc_o.amount_usd AS amount,
				'' AS Inv_no,
				'USD' AS currency,
				note AS note
			FROM `tabLC Open` lc_o 
			WHERE lc_o.group_id = %s

			UNION ALL

			SELECT
				lc_p.group_id AS name,
				'LC Paid' AS Type,
				'pay' AS t_type,
				lc_p.date AS Date,
				lc_p.amount_usd AS amount,
				'' AS Inv_no,
				'USD' AS currency,
				note AS note
			FROM `tabLC Payment` lc_p 
			WHERE lc_p.group_id = %s
					   
			UNION ALL

			SELECT
				imp_ln.group_id AS name,
				'Import Loan' AS Type,
				'pay' AS t_type,
				imp_ln.loan_date AS Date,
				imp_ln.loan_amount_usd AS amount,
				'' AS Inv_no,
				'USD' AS currency,
				note AS note
			FROM `tabImport Loan` imp_ln 
			WHERE imp_ln.group_id = %s AND imp_ln.from_lc_open=1
					   
			UNION ALL

			SELECT
				usance_lc.group_id AS name,
				'Usance LC' AS Type,
				'pay' AS t_type,
				usance_lc.usance_lc_date AS Date,
				usance_lc.usance_lc_amount_usd AS amount,
				'' AS Inv_no,
				'USD' AS currency,
				note AS note
			FROM `tabUsance LC` usance_lc
			WHERE usance_lc.group_id = %s AND usance_lc.from_lc_open=1
					   
			
			

		""", (name, name, name, name), as_dict=1)


	elif dc_name == "c_loan":
		return frappe.db.sql("""
			SELECT name, 'Cash Loan' AS Type,'rec' AS t_type, cash_loan_date AS Date, cash_loan_amount AS amount, '' AS Inv_no, currency, note AS note
			FROM `tabCash Loan` WHERE name=%s
			UNION ALL
			SELECT c_l_p.name, 'Cash Loan Paid', 'pay', c_l_p.payment_date , c_l_p.amount, c_l.cash_loan_no AS Inv_no, c_l_p.currency, c_l_p.note AS note 
			FROM `tabCash Loan Payment` c_l_p LEFT JOIN `tabCash Loan` c_l ON c_l_p.cash_loan_no= c_l.name WHERE c_l_p.cash_loan_no=%s
		""", (name, name), as_dict=1)

	elif dc_name == "imp_l":
		return frappe.db.sql("""
			SELECT name, 'Import Loan' AS Type, 'rec' AS t_type, loan_date AS Date, loan_amount AS amount, inv_no AS Inv_no, currency, note AS note
			FROM `tabImport Loan` WHERE name=%s
			UNION ALL
			SELECT imp_l_p.name, 'Imp Loan Payment', 'pay', imp_l_p.payment_date, imp_l_p.amount, imp_l.inv_no, imp_l.currency, imp_l.note AS note
			FROM `tabImport Loan Payment` imp_l_p 
			LEFT JOIN `tabImport Loan` imp_l ON imp_l.name = imp_l_p.inv_no 
			WHERE imp_l_p.inv_no=%s
		""", (name, name), as_dict=1)
	
	elif dc_name == "u_lc":
		return frappe.db.sql("""
			SELECT name, 'U LC' AS Type, 'rec' AS t_type, usance_lc_date AS Date, usance_lc_amount AS amount, inv_no AS Inv_no, currency, note AS note
			FROM `tabUsance LC` WHERE name=%s
			UNION ALL
			SELECT u_lc_p.name, 'U LC Payment', 'pay', u_lc_p.payment_date , u_lc_p.amount, u_lc.inv_no, u_lc_p.currency, u_lc_p.note AS note
			FROM `tabUsance LC Payment` u_lc_p 
			LEFT JOIN `tabUsance LC` u_lc ON u_lc.name = u_lc_p.inv_no 
			WHERE u_lc_p.inv_no=%s
		""", (name, name), as_dict=1)

	return "Error"


def build_rows(entries):
	balance = 0
	rows = []
	row_style= ""

	for e in entries:
		type_ = e["Type"]
		amount = e["amount"] or 0
		note = e["note"] or ""
		if e["t_type"]== "pay":
			balance -= amount
			row_style = "color:red;"
		else:
			balance += amount
			row_style= ""
		
		
			
		# Row HTML
		rows.append(f"""
			<tr style="{row_style}">
				<td>{e['Date']}</td>
				<td>{e['Inv_no']}</td>
				<td style="text-align:right;">{amount:,.2f}</td>
				<td>{type_}</td>
				<td style="text-align:right;">{balance:,.2f}</td>
				<td style="text-align:left;">{note}</td>
			</tr>
		""")

	return rows[-10:], balance


def build_buttons(dc_name, lc_no, balance):
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

    if dc_name == "lc_o" and balance > 0:
        company, bank = [p.strip() for p in lc_no.split(":")]
        buttons_html += quick_btn("LC Paid", "LC Payment",
                                  company=company, date=today_str, bank=bank)
        buttons_html += quick_btn("To Import Loan", "Import Loan",
                                  company=company, date=today_str, bank=bank, from_lc_open=1)
        buttons_html += quick_btn("To Usance LC", "Usance LC",
                                  company=company, date=today_str, bank=bank, from_lc_open=1)

    elif dc_name == "imp_l" and balance > 0:
        buttons_html += quick_btn("Imp Loan Payment", "Import Loan Payment",
                                  inv_no=lc_no, payment_date=today_str, amount=balance)

    elif dc_name == "u_lc" and balance > 0:
        buttons_html += quick_btn("U LC Payment", "Usance LC Payment",
                                  inv_no=lc_no, payment_date=today_str, amount=balance)

    elif dc_name == "c_loan" and balance > 0:
        buttons_html += quick_btn("Cash Loan Payment", "Cash Loan Payment",
                                  cash_loan_no=lc_no, payment_date=today_str, amount=balance)

    # return f'<div id="lc-buttons" style="margin-top: 12px; right: 10px; float:right;">{buttons_html}</div>'
    return f'<div id="lc-buttons" style="margin-top:30px; float:right;">{buttons_html}</div>'



def build_html(supplier_name, bank_name, term, rows_html, buttons_html):
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
				<th style="width:15%; text-align:center;">Date</th>
				<th style="width:20%; text-align:center;">Inv No</th>
				<th style="width:15%; text-align:center;">Amount</th>
				<th style="width:15%; text-align:center;">Details</th>
				<th style="width:15%; text-align:center;">Balance</th>			
				<th style="width:20%; text-align:center;">Note</th>
			</tr>
		</thead>
		<tbody>
			{''.join(rows_html)}
		</tbody>
	</table>
	{buttons_html}
	<div style="text-align:right; margin-top:12px; padding:8px; border-top:1px solid #eee;"></div>
	"""

