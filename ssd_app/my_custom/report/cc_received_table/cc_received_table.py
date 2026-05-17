# Copyright (c) 2026, SSDolui and contributors
# For license information, please see license.txt

import frappe

def get_data(filters):
	year= filters.get("year")
	limit= filters.get("limit")
	limit_clause = ""
	if limit and int(limit) > 0:
		limit_clause = f"LIMIT {int(limit)}"
	if not year:
		max_year = frappe.db.sql("""
            SELECT MAX(YEAR(date))
            FROM `tabCC Received`
            WHERE date IS NOT NULL
        """, as_list=True)[0][0]
		conditional_filter= f"""WHERE YEAR(ccr.date)= {int(max_year)}"""
	elif year =="All":
		conditional_filter=""
	else:
		conditional_filter= f"""WHERE YEAR(ccr.date)= {int(year)}"""
	

	data= frappe.db.sql(f"""
	SELECT
	ccr.name,
	ccr.date, 
	cus.customer, 
	ccr.entry_type, 
	ccr.amount_usd, 
	JSON_ARRAYAGG(JSON_OBJECT(ccb.ref_no, ROUND(ccb.amount,2))) AS details, 
	ccr.note, "-" AS action
	FROM `tabCC Received` ccr
	LEFT JOIN `tabCC Breakup` ccb ON ccr.name=ccb.parent
	LEFT JOIN `tabCustomer` cus ON cus.name= ccr.customer
	{conditional_filter}
	GROUP BY ccr.name
    ORDER BY ccr.creation DESC 
    {limit_clause};
	""", as_dict=True)
	return data


def execute(filters=None):

	data= get_data(filters)
	
	columns = [
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 200},
		{"label": "Entry Type", "fieldname": "entry_type", "fieldtype": "Data", "width": 110},
        {"label": "Received", "fieldname": "amount_usd", "fieldtype": "Float", "width": 100},
        {"label": "Details", "fieldname": "details", "fieldtype": "Data", "width": 400},
		{"label": "Naration", "fieldname": "note", "fieldtype": "Data", "width": 400},
        {"label": "Action", "fieldname": "action", "fieldtype": "Data", "width": 80}
    ]
	return columns, data


@frappe.whitelist()
def get_years():
    years = frappe.db.sql("""
        SELECT DISTINCT YEAR(date) AS year
        FROM `tabCC Received`
        WHERE date IS NOT NULL
        ORDER BY year ASC
    """, as_dict=True)

    # Return a simple list of years as strings
    return [str(d.year) for d in years]
