# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today



def execute(filters=None):

	columns = [
		{"label": "Inv/LC No", "fieldname": "inv_no", "fieldtype": "Data", "width": 85},
		{"label": "Date", "fieldname": "inv_date", "fieldtype": "Date", "width": 110},
		{"label": "Com", "fieldname": "com", "fieldtype": "Data", "width": 130},
		{"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 60},
		{"label": "P Term", "fieldname": "p_term", "fieldtype": "Data", "width": 80},
		{"label": "Amount", "fieldname": "nego", "fieldtype": "Float", "width": 100},
	]

	data = frappe.db.sql(f"""
		SELECT
			cif.name,
			cif.inv_no,
			cif.inv_date,
			bank.bank,
			cif.payment_term AS p_term,
			com.company_code AS com,
			GREATEST(IFNULL(nego.total_nego, 0) - IFNULL(ref.total_ref,0) - IFNULL(rec.total_rec, 0), 0) AS nego
		FROM `tabCIF Sheet` cif
		LEFT JOIN (
			SELECT inv_no, SUM(nego_amount) AS total_nego, MIN(bank_due_date) AS bank_due_date, MIN(due_date_confirm) AS due_date_confirm, MIN(name) AS nego_name
			FROM `tabDoc Nego` WHERE nego_date <= %(as_on)s GROUP BY inv_no
		) nego ON cif.name = nego.inv_no
		LEFT JOIN (
			SELECT inv_no, SUM(refund_amount) AS total_ref
			FROM `tabDoc Refund` WHERE refund_date <= %(as_on)s GROUP BY inv_no
		) ref ON cif.name = ref.inv_no
		LEFT JOIN (
			SELECT inv_no, SUM(received) AS total_rec
			FROM `tabDoc Received` WHERE received_date <= %(as_on)s GROUP BY inv_no
		) rec ON cif.name = rec.inv_no
		LEFT JOIN `tabBank` bank ON cif.bank = bank.name
		LEFT JOIN `tabCompany`com on com.name= cif.shipping_company
		WHERE cif.inv_date <= %(as_on)s
		AND 
			GREATEST(IFNULL(nego.total_nego, 0) - IFNULL(ref.total_ref,0) - IFNULL(rec.total_rec, 0), 0)>0
		ORDER BY cif.inv_no ASC
	""", {"as_on": today()}, as_dict=1)

# 	"""
# 	SELECT lco.lc_no AS inv_no,lco.lc_open_date AS date, lco.company AS com, lco.bank AS bank, 'LC Open' AS p_term, 

# GREATEST(amount_usd - IFNULL(lcp.lcp_amount / lco.ex_rate, 0) - IFNULL(ulc.ulc_amount / lco.ex_rate, 0) - IFNULL(impl.impl_amount / lco.ex_rate, 0),0) AS nego
# FROM `tabLC Open` lco
# LEFT JOIN (
# 			SELECT lc_no, SUM(amount) AS lcp_amount 
# 			FROM `tabLC Payment` 
# 			GROUP BY lc_no
# 		) lcp ON lcp.lc_no = lco.name
# LEFT JOIN (
# 			SELECT lc_no, SUM(usance_lc_amount) AS ulc_amount 
# 			FROM `tabUsance LC` 
# 			GROUP BY lc_no
# 		)ulc ON ulc.lc_no = lco.name
		
# LEFT JOIN (
# 			SELECT lc_no, SUM(loan_amount) AS impl_amount 
# 			FROM `tabImport Loan` 
# 			GROUP BY lc_no
# 		)impl ON impl.lc_no = lco.name
# WHERE GREATEST(amount_usd - IFNULL(lcp.lcp_amount / lco.ex_rate, 0) - IFNULL(ulc.ulc_amount / lco.ex_rate, 0) - IFNULL(impl.impl_amount / lco.ex_rate, 0),0)>0
	
# 	"""

	return columns, data
