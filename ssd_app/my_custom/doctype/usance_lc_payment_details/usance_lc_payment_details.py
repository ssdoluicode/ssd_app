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
        FROM `tabUsance LC Payment`
        WHERE (usance_lc_payment_details != 1 OR usance_lc_payment_details IS NULL)
        AND name LIKE %s
        ORDER BY name ASC
        LIMIT %s OFFSET %s
    """, values)



@frappe.whitelist()
def get_lc_data(lc_payment_id):
    payment = frappe.get_doc("Usance LC Payment", lc_payment_id)
    open = frappe.get_doc("Usance LC", payment.inv_no)
	
    bank_name = frappe.db.get_value("Bank", open.bank, "bank")
    com = frappe.db.get_value("Company", open.company, "company_code")
	
    # Return only the required fields
    return {
        "amount": payment.amount,
        "date": payment.payment_date,
        "com":com,
        "bank_name": bank_name,
        "currency": open.currency,
    }



class UsanceLCPaymentDetails(Document):
    def before_save(self):
        if self.lc_payment_id:
            frappe.db.set_value("Usance LC Payment", self.lc_payment_id, "usance_lc_payment_details", 1)		
    def on_trash(self):
        if self.lc_payment_id:
            frappe.db.set_value("Usance LC Payment", self.lc_payment_id, "usance_lc_payment_details", 0)		

