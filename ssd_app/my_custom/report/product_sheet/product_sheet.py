# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

# import frappe


import frappe

def execute(filters=None):

    query = f"""
    SELECT 
    sb.inv_no,
    pc.product_category,
    pg.product_group,
    p.product,
    cif_p.sc_no, 
    cif_p.qty, 
    u.unit, 
    cif_p.rate AS e_rate, 
    cif_p.gross AS e_gross, 
    cif_p.charges AS e_charges, 
    cif_p.currency AS e_curr, 
    cif_p.ex_rate AS e_ex_rate,
    cif_p.gross_usd AS e_gross_usd, 
    cost_p.rate AS i_rate, 
    cost_p.gross AS i_gross, 
    cost_p.charges AS i_charges, 
    cost_p.currency AS i_curr, 
    cost_p.ex_rate AS i_ex_rate,
    cost_p.gross_usd AS i_gross_usd 
	FROM `tabProduct CIF` cif_p 
	LEFT JOIN `tabProduct Cost` cost_p ON cif_p.name = cost_p.id_code
    LEFT JOIN `tabCIF Sheet` cif ON cif.name= cif_p.parent
    LEFT JOIN `tabShipping Book` sb ON sb.name= cif.inv_no
    LEFT JOIN `tabProduct` p ON p.name = cif_p.product
    LEFT JOIN `tabProduct Group`  pg ON pg.name= p.product_group
    LEFT JOIN `tabProduct Category`  pc ON pc.name= pg.product_category
    LEFT Join `tabUnit` u ON u.name= cif_p.unit
    """

    data = frappe.db.sql(query, as_dict=1)

    columns = [
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
        {"label": "Category", "fieldname": "product_category", "fieldtype": "Data", "width": 140},
        {"label": "Product Group", "fieldname": "product_group", "fieldtype": "Data", "width": 160},
        {"label": "Product", "fieldname": "product", "fieldtype": "Data", "width": 150},
        {"label": "SC No", "fieldname": "sc_no", "fieldtype": "Data", "width": 90},
        {"label": "Qty", "fieldname": "qty", "fieldtype": "Data", "width": 90},
        {"label": "Unit", "fieldname": "unit", "fieldtype": "Data", "width": 60},
        {"label": "S Rate", "fieldname": "e_rate", "fieldtype": "Float", "width": 90},
        {"label": "Gross", "fieldname": "e_gross", "fieldtype": "Float", "width": 90},
        {"label": "Charges", "fieldname": "e_charges", "fieldtype": "Float", "width": 90},
        {"label": "S Curr", "fieldname": "e_curr", "fieldtype": "Data", "width": 80},
        {"label": "S ExR", "fieldname": "e_ex_rate", "fieldtype": "Float", "width": 80},
        {"label": "G Sales", "fieldname": "e_gross_usd", "fieldtype": "Float", "width": 110},
        
    ]

    return columns, data
