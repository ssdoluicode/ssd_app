# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe



def execute(filters=None):
    filters = filters or {}
    status_filter = filters.get("status", "Pending")   # default Pending
    type_filter = filters.get("type", "All")           # default All

    # Build WHERE clause based on status
    where_clause_lcp = "WHERE 1=1"
    where_clause_ulcp = "WHERE 1=1"
    where_clause_impl = "WHERE 1=1"
    where_clause_implp = "WHERE 1=1"

    # Status filter
    if status_filter == "Pending":
        where_clause_lcp += " AND lcp.lc_payment_details != 1"
        where_clause_ulcp += " AND ulcp.usance_lc_payment_details != 1"
        where_clause_impl += " AND impl.import_loan_details != 1"
        where_clause_implp += " AND implp.import_loan_payment_details != 1"

    elif status_filter == "Updated":
        where_clause_lcp += " AND lcp.lc_payment_details = 1"
        where_clause_ulcp += " AND ulcp.usance_lc_payment_details = 1"
        where_clause_impl += " AND impl.import_loan_details = 1"
        where_clause_implp += " AND implp.import_loan_payment_details = 1"

    # Type filter (show only selected table)
    if type_filter == "LC Payment":
        where_clause_lcp += " AND 1=1"
        where_clause_ulcp += " AND 1=0"
        where_clause_impl += " AND 1=0"
        where_clause_implp += " AND 1=0"
    
    elif type_filter == "U LC Payment":
        where_clause_lcp += " AND 1=0"
        where_clause_ulcp += " AND 1=1"
        where_clause_impl += " AND 1=0"
        where_clause_implp += " AND 1=0"
        
    elif type_filter == "Imp Loan":
        where_clause_lcp += " AND 1=0"
        where_clause_ulcp += " AND 1=0"
        where_clause_impl += " AND 1=1"
        where_clause_implp += " AND 1=0"

    elif type_filter == "Imp Loan Payment":
        where_clause_lcp += " AND 1=0"
        where_clause_ulcp += " AND 1=0"
        where_clause_impl += " AND 1=0"
        where_clause_implp += " AND 1=1"
    
	

	# Build WHERE clause based on status
   
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
			"LC Payment" AS type,
            lcp.lc_payment_details AS details
		FROM `tabLC Payment` lcp
		LEFT JOIN `tabBank` bank ON bank.name = lcp.bank
		LEFT JOIN `tabCompany` com ON com.name = lcp.company
		{where_clause_lcp}

		UNION ALL

		SELECT 
			ulcp.name,
			ulcp.payment_date AS date,
			bank.bank AS bank,
			com.company_code AS com,
			ulc.currency AS curr,
			ulcp.amount AS amount,
			"U LC Payment" AS type,
            ulcp.usance_lc_payment_details AS details
		FROM `tabUsance LC Payment` ulcp
		LEFT JOIN `tabUsance LC` ulc ON ulc.name = ulcp.inv_no
		LEFT JOIN `tabBank` bank ON bank.name = ulc.bank
		LEFT JOIN `tabCompany` com ON com.name = ulc.company
		{where_clause_ulcp}


		UNION ALL

		SELECT 
			impl.name,
			impl.loan_date AS date,
			bank.bank AS bank,
			com.company_code AS com,
			impl.currency AS curr,
			impl.loan_amount AS amount,
			"Imp Loan" AS type,
            impl.import_loan_details AS details
		FROM `tabImport Loan` impl
		LEFT JOIN `tabBank` bank ON bank.name = impl.bank
		LEFT JOIN `tabCompany` com ON com.name = impl.company
		{where_clause_impl}

		UNION ALL

		SELECT 
			implp.name,
			implp.payment_date AS date,
			bank.bank AS bank,
			com.company_code AS com,
			impl.currency AS curr,
			implp.amount AS amount,
			"Imp Loan Payment" AS type,
            implp.import_loan_payment_details AS details
		FROM `tabImport Loan Payment` implp
		LEFT JOIN `tabImport Loan` impl ON impl.name = implp.inv_no
		LEFT JOIN `tabBank` bank ON bank.name = impl.bank
		LEFT JOIN `tabCompany` com ON com.name = impl.company
		{where_clause_implp}

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
        {"label": "Type", "fieldname": "type", "fieldtype": "Data", "width": 180},
    ]

    return columns, data
