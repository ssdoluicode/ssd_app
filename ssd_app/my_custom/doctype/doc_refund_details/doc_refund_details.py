# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


def set_calculated_fields(doc):
    inv_id= frappe.db.get_value("Doc Refund", doc.inv_no, "inv_no")
    invoice, shi_id = frappe.db.get_value(
        "Doc Nego",
        {"inv_no": inv_id},
        ["invoice_no", "inv_no"]
    )
    doc.invoice_no = invoice
    doc.custom_title = f"{doc.name} ({invoice})"
    doc.shipping_id = shi_id

class DocRefundDetails(Document):
    def before_save(self):
        if self.inv_no:
            set_calculated_fields(self)
            frappe.db.set_value("Doc Refund", self.inv_no, "refund_details", 1)		
    def on_trash(self):
        if self.inv_no:
            frappe.db.set_value("Doc Refund", self.inv_no, "refund_details", 0)	


@frappe.whitelist()
def get_available_inv_no(doctype, txt, searchfield, start, page_len, filters):

    txt = f"%{txt}%"
    values = (txt, page_len, start)

    return frappe.db.sql(f"""
        SELECT
            name, custom_title
        FROM `tabDoc Refund`
        WHERE (refund_details != 1 OR refund_details IS NULL)
        AND custom_title LIKE %s
        ORDER BY custom_title ASC
        LIMIT %s OFFSET %s
    """, values)

