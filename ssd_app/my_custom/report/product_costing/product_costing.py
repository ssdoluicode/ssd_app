# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import fmt_money
from datetime import date, timedelta
# from ssd_app.utils.auto_excel_report import generate_daily_banking



def get_today_str():
    return date.today().strftime("%Y-%m-%d")

def execute(filters=None):
    if not filters:
        filters = {}

    year = filters.get("year")

    # Determine year condition
    if not year:
        max_year = frappe.db.sql("""
            SELECT MAX(YEAR(inv_date))
            FROM `tabCIF Sheet`
            WHERE inv_date IS NOT NULL
        """, as_list=True)[0][0]

        conditional_filter = f"WHERE YEAR(cif.inv_date) = {int(max_year)}"

    elif year == "All":
        conditional_filter = ""

    else:
        conditional_filter = f"WHERE YEAR(cif.inv_date) = {int(year)}"

    # Main Query
    data = frappe.db.sql(f"""
	SELECT 
    cif.name AS cif_id,
    cif.invoice_no AS inv_no,
    cif.inv_date,
    cus.code AS customer,
    noti.code AS notify,
    sup.code AS supplier,
    pc.product_category AS category,
    pg.product_group,
    p.product, 
    cifp.qty, 
    u.unit, 
    cifp.currency AS curr, 
    cifp.ex_rate, 
    cifp.rate, 
    cifp.gross, 
    cifp.gross_usd AS g_sales,
    costp.rate AS b_rate,
    costp.currency AS b_curr,
    costp.ex_rate AS b_ex_rate,
    costp.gross AS b_gross,
    costp.gross_usd AS pur,
    (cifp.gross_usd - costp.gross_usd) AS margin             

FROM `tabProduct CIF` cifp
/* Join directly instead of using a Subquery to utilize indexes on 'parent' */
INNER JOIN `tabCIF Sheet` cif 
    ON cif.name = cifp.parent

/* Moved 'tabProduct Cost' up to keep the core data linkage tight */
LEFT JOIN `tabProduct Cost` costp 
    ON costp.id_code = cifp.name

/* Join master data tables directly */
LEFT JOIN `tabShipping Book` sb ON sb.name = cif.inv_no
LEFT JOIN `tabCustomer` cus ON cus.name = sb.customer
LEFT JOIN `tabNotify` noti ON noti.name = sb.notify
LEFT JOIN `tabSupplier` sup ON sup.name = costp.supplier
LEFT JOIN `tabProduct` p ON p.name = cifp.product
LEFT JOIN `tabProduct Group` pg ON pg.name = p.product_group
LEFT JOIN `tabProduct Category` pc ON pc.name = cif.category
LEFT JOIN `tabUnit` u ON u.name = cifp.unit
{conditional_filter}
ORDER BY cif.inv_date DESC;

	""", as_dict=1)
    
    columns = [
		{"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 85},
		{"label": "Inv Date", "fieldname": "inv_date", "fieldtype": "Date", "width": 110},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 120},
		{"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 180},
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 180},
        {"label": "Category", "fieldname": "category", "fieldtype": "Data", "width": 180},
        {"label": "P Group", "fieldname": "product_group", "fieldtype": "Data", "width": 180},
		{"label": "Product", "fieldname": "product", "fieldtype": "Data", "width": 100},
		{"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 100},
        {"label": "Unit", "fieldname": "unit", "fieldtype": "Data", "width": 60},
        {"label": "S Rate", "fieldname": "rate", "fieldtype": "Float", "width": 115},
		{"label": "S Curr", "fieldname": "curr", "fieldtype": "Data", "width": 70},
		{"label": "S Ex Rate", "fieldname": "ex_rate", "fieldtype": "Float", "width": 95},
		{"label": "S Gross", "fieldname": "gross", "fieldtype": "Float", "width": 110},
        {"label": "G Sales", "fieldname": "g_sales", "fieldtype": "Float", "width": 110},
        {"label": "B Rate", "fieldname": "b_rate", "fieldtype": "Float", "width": 115},
        {"label": "B Curr", "fieldname": "b_curr", "fieldtype": "Data", "width": 70},
        {"label": "B Ex Rate", "fieldname": "b_ex_rate", "fieldtype": "Float", "width": 95},
        {"label": "B Gross", "fieldname": "b_gross", "fieldtype": "Float", "width": 110},
        {"label": "Purchase", "fieldname": "pur", "fieldtype": "Float", "width": 110},
        {"label": "Margin", "fieldname": "margin", "fieldtype": "Float", "width": 110},
	]

    return columns, data

