# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

# import frappe


import frappe

def execute(filters=None):

    query = f"""
    SELECT cif_p.parent, cif_p.product,cif_p.sc_no, cif_p.qty, cif_p.unit, cif_p.rate AS e_rate, 
    cif_p.gross AS e_gross, cif_p.charges AS e_charges, cif_p.currency AS e_curr, cif_p.ex_rate AS e_ex_rate,
    cif_p.gross_usd AS e_gross_usd, cost_p.rate AS i_rate, cost_p.gross AS i_gross, cost_p.charges AS i_charges, 
    cost_p.currency AS i_curr, cost_p.ex_rate AS i_ex_rate,cost_p.gross_usd AS i_gross_usd 
    FROM `tabProduct CIF` cif_p LEFT JOIN `tabProduct Cost`cost_p ON cif_p.name=cost_p.id_code

    """

    data = frappe.db.sql(query, as_dict=1)

    columns = [
        {"label": "Inv No", "fieldname": "parent", "fieldtype": "Data", "width": 90},
        {"label": "product", "fieldname": "product", "fieldtype": "Data", "width": 110},
        
    ]

    return columns, data
