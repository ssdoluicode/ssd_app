# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


@frappe.whitelist()
def get_available_inv_no(doctype, txt, searchfield, start, page_len, filters):

    txt = f"%{txt}%"
    values = (txt, page_len, start)

    return frappe.db.sql(f"""
        SELECT
            name, custom_title
        FROM `tabDoc Nego`
        WHERE (nego_details != 1 OR nego_details IS NULL)
        AND custom_title LIKE %s
        ORDER BY custom_title ASC
        LIMIT %s OFFSET %s
    """, values)



@frappe.whitelist()
def get_nego_data(name):
    doc = frappe.get_doc("Doc Nego", name)
    
    bank_name = frappe.db.get_value("Bank", doc.bank, "bank")
    
    # Return only the required fields
    return {
        "nego_amount": doc.nego_amount,
        "nego_date": doc.nego_date,
        "bank_name": bank_name,
        "payment_term": f"{doc.payment_term} - {doc.term_days or ''}" if doc.payment_term in ["DA", "LC"] else doc.payment_term
    }

def set_calculated_fields(doc):
    invoice = frappe.db.get_value("Doc Nego", doc.inv_no, "invoice_no")
    doc.invoice_no = invoice

class DocNegoDetails(Document):

    # when create/update
    def before_save(self):
        if self.inv_no:
            set_calculated_fields(self)
            frappe.db.set_value("Doc Nego", self.inv_no, "nego_details", 1)

    # when delete
    def on_trash(self):
        if self.inv_no:
            frappe.db.set_value("Doc Nego", self.inv_no, "nego_details", 0)