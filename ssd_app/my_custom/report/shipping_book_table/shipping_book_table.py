# Copyright (c) 2026, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import formatdate, flt
from frappe.utils.pdf import get_pdf
from frappe.utils.jinja import render_template
from frappe import _


def get_cif_data(filters):
    year = filters.year
    limit = filters.get("limit")
    status = filters.get("status")
    
    limit_clause = ""
    if limit and int(limit) > 0: 
        limit_clause = f"LIMIT {int(limit)}"

    conditional_filter = "WHERE 1=1"
    if not year:
        max_year = frappe.db.sql("""
            SELECT MAX(YEAR(bl_date))
            FROM `tabShipping Book`
            WHERE bl_date IS NOT NULL
        """, as_list=True)[0][0]
        conditional_filter += f""" AND YEAR(sb.bl_date)= {int(max_year)}"""
    else:
        conditional_filter += f""" AND YEAR(sb.bl_date)= {int(year)}"""
        
    if(status =="cif_pending"):
        conditional_filter += " AND cif.name IS NULL "
    elif(status =="cif_done"):
        conditional_filter += " AND cif.name IS NOT NULL "
        
    data= frappe.db.sql(f"""
        SELECT sb.name, sb.inv_no, sb.bl_date, com.company_code AS s_com, cus.customer, noti.notify, sb.invoice_amount, sb.document, 
                        term.term_name AS p_term, sb.term_days, bank.bank, user.first_name AS created_by, cif.name AS cif_id, "-" AS action
FROM `tabShipping Book` sb
LEFT JOIN `tabCompany` com ON com.name= sb.company
LEFT JOIN `tabCustomer` cus ON cus.name= sb.customer
LEFT JOIN `tabNotify` noti ON noti.name= sb.notify
LEFT JOIN `tabPayment Term` term ON term.name= sb.payment_term
LEFT JOIN `tabBank` bank ON bank.name= sb.bank
LEFT JOIN `tabUser` AS user ON sb.owner= user.name
LEFT JOIN `tabCIF Sheet` cif ON cif.inv_no= sb.name

    {conditional_filter}
    ORDER BY sb.creation DESC 
    {limit_clause};
    """, as_dict=1)
    return data


def execute(filters=None):
    columns = [
        # {"label": "Inv ID", "fieldname": "name", "fieldtype": "Data", "width": 80},
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
        {"label": "BL Date", "fieldname": "bl_date", "fieldtype": "Date", "width": 110},
        {"label": "Shi Com", "fieldname": "s_com", "fieldtype": "Data", "width": 110},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 180},
        {"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 220},
        {"label": "Invoice", "fieldname": "invoice_amount", "fieldtype": "Float", "width": 100},
        {"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 100},
        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 60},
        {"label": "P Term", "fieldname": "p_term", "fieldtype": "Data", "width": 100},
        {"label": "T Days", "fieldname": "term_days", "fieldtype": "Data", "width": 80},
        {"label": "Create By", "fieldname": "created_by", "fieldtype": "Data", "width": 80},
        {"label": "Action", "fieldname": "action", "fieldtype": "Data", "width": 80}
    ]
    data = get_cif_data(filters)
    return columns, data

@frappe.whitelist()
def get_years():
    years = frappe.db.sql("""
        SELECT DISTINCT YEAR(bl_date) AS year
        FROM `tabShipping Book`
        WHERE bl_date IS NOT NULL
        ORDER BY year ASC
    """, as_dict=True)

    # Return a simple list of years as strings
    return [str(d.year) for d in years]
