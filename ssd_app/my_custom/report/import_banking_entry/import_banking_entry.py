# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe



def execute(filters=None):
    filters = filters or {}
    status_filter = filters.get("status", "Pending")   # default Pending
    type_filter = filters.get("type", "All")           # default All

    # Build WHERE clause based on status
    where_clause_nego = "WHERE 1=1"
    where_clause_ref = "WHERE 1=1"
    where_clause_rec = "WHERE 1=1"

    # Status filter
    if status_filter == "Pending":
        where_clause_nego += " AND nego.nego_details != 1"
        where_clause_ref += " AND ref.refund_details != 1"
        where_clause_rec += " AND rec.rec_details != 1"

    elif status_filter == "Updated":
        where_clause_nego += " AND nego.nego_details = 1"
        where_clause_ref += " AND ref.refund_details = 1"
        where_clause_rec += " AND rec.rec_details = 1"

    # Type filter (show only selected table)
    if type_filter == "Nego":
        where_clause_nego += " AND 1=1"
        where_clause_ref += " AND 1=0"
        where_clause_rec += " AND 1=0"

    elif type_filter == "Refund":
        where_clause_nego += " AND 1=0"
        where_clause_ref += " AND 1=1"
        where_clause_rec += " AND 1=0"

    elif type_filter == "Received":
        where_clause_nego += " AND 1=0"
        where_clause_ref += " AND 1=0"
        where_clause_rec += " AND 1=1"
	

	# Build WHERE clause based on status
    """
    SELECT 
	lcp.date AS date, bank.bank AS bank, com.company_code AS com, lcp.currency AS curr, lcp.amount AS amount, "LC Paid" AS type
	FROM `tabLC Payment` lcp
	LEFT JOIN `tabBank` bank ON bank.name= lcp.bank
	LEFT JOIN `tabCompany` com ON com.name=lcp.company
	WHERE lcp.lc_payment_details=0
    
    UNION ALL
    
    SELECT 
	ulcp.payment_date AS date, bank.bank AS bank, com.company_code AS com, ulc.currency AS curr, ulcp.amount AS amount, "U LC Payment" AS type
	FROM `tabUsance LC Payment` ulcp
	LEFT JOIN `tabUsance LC` ulc ON ulc.name= ulcp.inv_no
	LEFT JOIN `tabBank` bank ON bank.name= ulc.bank
	LEFT JOIN `tabCompany` com ON com.name=ulc.company
	WHERE ulcp.usance_lc_payment_details=0
    
    UNION ALL
    
    SELECT
	impl.loan_date AS date, bank.bank AS bank, com.company_code AS com, impl.currency AS curr, impl.loan_amount AS amount, "Imp Loan" AS term
	FROM `tabImport Loan` impl
	LEFT JOIN `tabBank` bank ON bank.name= impl.bank
	LEFT JOIN `tabCompany` com ON com.name=impl.company
	WHERE impl.import_loan_details=0
    
    UNION ALL
    
    SELECT implp.payment_date AS date, bank.bank AS bank, com.company_code AS com, impl.currency AS curr, implp.amount AS amount, "Imp Loan Payment" AS term
	FROM `tabImport Loan Payment` implp
	LEFT JOIN `tabImport Loan` impl ON impl.name= implp.inv_no
	LEFT JOIN `tabBank` bank ON bank.name= impl.bank
	LEFT JOIN `tabCompany` com ON com.name=impl.company
	WHERE implp.import_loan_payment_details=0
    """
  

    query = f"""
	SELECT *
	FROM (
		SELECT 
			lcp.name,
			lcp.date AS date,
			bank.bank AS bank,
			com.company_code AS com,
			lcp.currency AS curr,
			lcp.amount AS amount,
			"LC Paid" AS type
		FROM `tabLC Payment` lcp
		LEFT JOIN `tabBank` bank ON bank.name = lcp.bank
		LEFT JOIN `tabCompany` com ON com.name = lcp.company
		WHERE lcp.lc_payment_details = 0

		UNION ALL

		SELECT 
			ulcp.name,
			ulcp.payment_date AS date,
			bank.bank AS bank,
			com.company_code AS com,
			ulc.currency AS curr,
			ulcp.amount AS amount,
			"U LC Payment" AS type
		FROM `tabUsance LC Payment` ulcp
		LEFT JOIN `tabUsance LC` ulc ON ulc.name = ulcp.inv_no
		LEFT JOIN `tabBank` bank ON bank.name = ulc.bank
		LEFT JOIN `tabCompany` com ON com.name = ulc.company
		WHERE ulcp.usance_lc_payment_details = 0

		UNION ALL

		SELECT 
			impl.name,
			impl.loan_date AS date,
			bank.bank AS bank,
			com.company_code AS com,
			impl.currency AS curr,
			impl.loan_amount AS amount,
			"Imp Loan" AS type
		FROM `tabImport Loan` impl
		LEFT JOIN `tabBank` bank ON bank.name = impl.bank
		LEFT JOIN `tabCompany` com ON com.name = impl.company
		WHERE impl.import_loan_details = 0

		UNION ALL

		SELECT 
			implp.name,
			implp.payment_date AS date,
			bank.bank AS bank,
			com.company_code AS com,
			impl.currency AS curr,
			implp.amount AS amount,
			"Imp Loan Payment" AS type
		FROM `tabImport Loan Payment` implp
		LEFT JOIN `tabImport Loan` impl ON impl.name = implp.inv_no
		LEFT JOIN `tabBank` bank ON bank.name = impl.bank
		LEFT JOIN `tabCompany` com ON com.name = impl.company
		WHERE implp.import_loan_payment_details = 0
	) t
	ORDER BY t.date ASC;

	"""


    data = frappe.db.sql(query, as_dict=1)

    columns = [
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 110},
        {"label": "Company", "fieldname": "com", "fieldtype": "Data", "width": 110},
        {"label": "Currency", "fieldname": "curr", "fieldtype": "Data", "width": 110},
        {"label": "Amount", "fieldname": "amount", "fieldtype": "Float", "width": 125},
        {"label": "Type", "fieldname": "type", "fieldtype": "Data", "width": 145},
    ]

    return columns, data
