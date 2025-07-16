# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
import pandas as pd


def execute(filters=None):
	quary= """
	SELECT * FROM (
    SELECT 
        cif.name,  
        cif.inv_no, 
        cif.inv_date, 
        com.company_code AS company,
        pcat.product_category AS category, 
        cus.customer AS customer, 
        noti.notify AS notify, 
        cif.sc_no, 
        cif.gross_sales,
        cif.handling_charges,
        cif.handling_pct, 
        cif.sales, 
        cif.document, 
        cif.cc, 
        bank.bank, 
        IF(cif.payment_term IN ('LC', 'DA'),
           CONCAT(cif.payment_term, '- ', cif.term_days),
           cif.payment_term) AS p_term, 
        cif.from_country AS f_country, 
        lport.port AS l_port, 
        cif.to_country AS t_country, 
        dport.port AS d_port
    FROM `tabCIF Sheet` cif
    LEFT JOIN `tabCompany` com ON cif.accounting_company = com.name
    LEFT JOIN `tabProduct Category` pcat ON cif.category = pcat.name
    LEFT JOIN `tabCustomer` cus ON cif.customer = cus.name
    LEFT JOIN `tabNotify` noti ON cif.notify = noti.name
    LEFT JOIN `tabBank` bank ON cif.bank = bank.name
    LEFT JOIN `tabPort` lport ON cif.load_port = lport.name
    LEFT JOIN `tabPort` dport ON cif.destination_port = dport.name
) cif_s
LEFT JOIN (
    SELECT 
        cost.inv_no AS cif_id, 
        cost.name AS cost_id, 
        cost.purchase, 
        cost.commission, 
        cost.agent, 
        cost.supplier, 
        cost.cost, 
        cost.profit, 
        cost.profit_pct 
    FROM `tabCost Sheet` cost
) cost_s ON cif_s.name = cost_s.cif_id

	"""

	data= frappe.db.sql(quary, as_dict=1)

	columns = [
		{"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
		{"label": "Inv Date", "fieldname": "inv_date", "fieldtype": "Date", "width": 110},
        {"label": "Com", "fieldname": "company", "fieldtype": "Data", "width": 110},
		{"label": "Category", "fieldname": "category", "fieldtype": "Data", "width": 110},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 110},
		{"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 110},
		{"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 110},
		{"label": "G Sales", "fieldname": "gross_sales", "fieldtype": "Float", "width": 110},
		{"label": "Handling", "fieldname": "handling_charges", "fieldtype": "Float", "width": 90},
		{"label": "Sales", "fieldname": "sales", "fieldtype": "Float", "width": 110},
		{"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 110},
		{"label": "CC", "fieldname": "cc", "fieldtype": "Float", "width": 110},
		{"label": "Purchase", "fieldname": "purchase", "fieldtype": "Float", "width": 110},
		{"label": "Freight", "fieldname": "Freight", "fieldtype": "Float", "width": 110},
		{"label": "Local Exp", "fieldname": "Local Exp", "fieldtype": "Float", "width": 110},
		{"label": "Comm", "fieldname": "commission", "fieldtype": "Float", "width": 110},
		{"label": "Other Exp", "fieldname": "other_exp", "fieldtype": "Float", "width": 110},
		{"label": "Cost", "fieldname": "cost", "fieldtype": "Float", "width": 110},
		{"label": "Profit", "fieldname": "profit", "fieldtype": "Float", "width": 110},
		{"label": "Profit %", "fieldname": "profit_pct", "fieldtype": "Float", "width": 110},
		{"label": "P Term", "fieldname": "p_term", "fieldtype": "Data", "width": 110},
		{"label": "F Country", "fieldname": "f_country", "fieldtype": "Data", "width": 110},
		{"label": "L Port", "fieldname": "l_port", "fieldtype": "Data", "width": 110},
		{"label": "T Country", "fieldname": "t_country", "fieldtype": "Data", "width": 110},
		{"label": "D Port", "fieldname": "d_port", "fieldtype": "Data", "width": 110},
		

	]


	exp_data = frappe.db.sql("""
		SELECT parent AS cost_id, expenses, amount_usd
		FROM `tabExpenses Cost`
	""", as_dict=True)


	df = pd.DataFrame([dict(row) for row in exp_data])
	exp_df = df.pivot_table(
		index='cost_id',
		columns='expenses',
		values='amount_usd',
		aggfunc='sum',
		fill_value=0
	)

	exp_df['other_exp'] = exp_df['Inland Charges'] + exp_df['Switch B/L Charges'] + exp_df['Others']
	exp_df= exp_df[[ "Freight", "Local Exp", "other_exp"]]
	exp_df = exp_df.reset_index()

	data_df = pd.DataFrame([dict(row) for row in data])
	# data_df= data_df.fillna(0)

	merged_df = data_df.merge(exp_df, on='cost_id', how='left')
	merged_df[["Freight", "Local Exp", "other_exp"]] =merged_df[["Freight", "Local Exp", "other_exp"]].fillna(0)

	merged_data = merged_df.to_dict(orient='records')

	return columns, merged_data
