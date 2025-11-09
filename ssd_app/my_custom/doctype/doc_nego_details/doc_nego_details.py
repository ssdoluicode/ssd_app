# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

@frappe.whitelist()
def get_available_inv_no(doctype, txt, searchfield, start, page_len, filters):
    used_inv = frappe.get_all("Doc Nego Details", pluck="inv_no")

    if used_inv:
        placeholders = ', '.join(['%s'] * len(used_inv))
        condition = f"WHERE name NOT IN ({placeholders}) AND invoice_no LIKE %s"
        values = used_inv + [f"%{txt}%"]
    else:
        condition = "WHERE invoice_no LIKE %s"
        values = [f"%{txt}%"]

    values += [page_len, start]

    return frappe.db.sql(f"""
        SELECT name, invoice_no
        FROM `tabDoc Nego`
        {condition}
        ORDER BY invoice_no ASC
        LIMIT %s OFFSET %s
    """, tuple(values))

@frappe.whitelist()
def get_nego_data(name):
    doc = frappe.get_doc("Doc Nego", name)
    
    bank_name = frappe.db.get_value("Bank", doc.bank, "bank")
    
    # Return only the required fields
    return {
        "nego_amount": doc.nego_amount,
        "nego_date": doc.nego_date,
        "bank_name": bank_name,
        "payment_term": doc.payment_term
    }




class DocNegoDetails(Document):
	pass
