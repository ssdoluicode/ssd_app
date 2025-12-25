# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

@frappe.whitelist()
def lc_id_filter(doctype, txt, searchfield, start, page_len, filters):

    txt = f"%{txt}%"
    values = (txt, page_len, start)

    return frappe.db.sql(f"""
        SELECT
            name
        FROM `tabLC Payment`
        WHERE (lc_payment_details != 1 OR lc_payment_details IS NULL)
        AND name LIKE %s
        ORDER BY name ASC
        LIMIT %s OFFSET %s
    """, values)



@frappe.whitelist()
def get_lc_data(lc_payment_id):
    doc = frappe.get_doc("LC Payment", lc_payment_id)
	
    bank_name = frappe.db.get_value("Bank", doc.bank, "bank")
    com = frappe.db.get_value("Company", doc.company, "company_code")
	
    # Return only the required fields
    return {
        "amount": doc.amount,
        "date": doc.date,
        "com":com,
        "bank_name": bank_name,
        "currency": doc.currency,
    }



class LCPaymentDetails(Document):
	pass
