# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
import pandas as pd


def execute(filters=None):
	quary= """SELECT  cif.inv_no, cif.inv_date, com.company_code AS company,pcat.product_category AS category, cus.customer AS customer, 
	noti.notify AS notify, cif.sc_no, cif.gross_sales,cif.handling_charges,cif.handling_pct, cif.sales, cif.document, cif.cc, bank.bank, 
	IF(cif.payment_term IN ('LC', 'DA'),
       CONCAT(cif.payment_term, '- ', cif.term_days),
       cif.payment_term) AS p_term, 
	cif.from_country AS f_country, lport.port AS l_port, cif.to_country AS t_country, dport.port AS d_port
	FROM `tabCIF Sheet` cif
	LEFT JOIN `tabCompany` com ON cif.accounting_company= com.name
	LEFT JOIN `tabProduct Category` pcat ON cif.category=pcat.name
	LEFT JOIN `tabCustomer` cus ON cif.customer= cus.name
	LEFT JOIN `tabNotify` noti ON cif.notify= noti.name
	LEFT JOIN `tabBank` bank ON cif.bank= bank.name
	LEFT JOIN `tabPort` lport ON cif.load_port= lport.name
	LEFT JOIN `tabPort` dport ON cif.destination_port= dport.name"""

	data= frappe.db.sql(quary, as_dict=1)

	columns = [
		{"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
		{"label": "Inv Date", "fieldname": "inv_date", "fieldtype": "Date", "width": 110},
        {"label": "Com", "fieldname": "company", "fieldtype": "Data", "width": 110},
		{"label": "Category", "fieldname": "category", "fieldtype": "Data", "width": 110},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 110},
		{"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 110},
		{"label": "G Sales", "fieldname": "gross_sales", "fieldtype": "Float", "width": 110},
		{"label": "Handling", "fieldname": "handling_charges", "fieldtype": "Float", "width": 90},
		{"label": "Sales", "fieldname": "sales", "fieldtype": "Float", "width": 110},
		{"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 110},
		{"label": "CC", "fieldname": "cc", "fieldtype": "Float", "width": 110},
		{"label": "P Term", "fieldname": "p_term", "fieldtype": "Data", "width": 110},
		{"label": "F Country", "fieldname": "f_country", "fieldtype": "Data", "width": 110},
		{"label": "L Port", "fieldname": "l_port", "fieldtype": "Data", "width": 110},
		{"label": "T Country", "fieldname": "t_country", "fieldtype": "Data", "width": 110},
		{"label": "D Port", "fieldname": "d_port", "fieldtype": "Data", "width": 110},

	]

	

	# n_data = frappe.db.sql("""
	# 	SELECT parent, expenses, amount_usd 
	# 	FROM `tabExpenses Cost`
	# """, as_dict=True)

	# df = pd.DataFrame(n_data)
	# pivot_df = df.pivot_table(
	# 	index='parent',
	# 	columns='expenses',
	# 	values='amount_usd',
	# 	aggfunc='sum',
	# 	fill_value=0
	# )

	# pivot_df['other_exp'] = pivot_df['Inland Charges'] + pivot_df['Switch B/L Charges'] + pivot_df['Others']

	# print(pivot_df)
	return columns, data
