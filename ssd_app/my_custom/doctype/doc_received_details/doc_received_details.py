# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import timedelta

@frappe.whitelist()
def get_available_inv_no(doctype, txt, searchfield, start, page_len, filters):

    txt = f"%{txt}%"
    values = (txt, page_len, start)

    return frappe.db.sql(f"""
        SELECT
            name, custom_title
        FROM `tabDoc Received`
        WHERE (rec_details != 1 OR rec_details IS NULL)
        AND custom_title LIKE %s
        ORDER BY custom_title ASC
        LIMIT %s OFFSET %s
    """, values)




def set_calculated_fields(doc):
    invoice, cif_id = frappe.db.get_value("Doc Received", doc.inv_no, ["invoice_no", "inv_no"])
    doc.invoice_no = invoice
    doc.cif_id= cif_id

class DocReceivedDetails(Document):
	# when create/update
    def before_save(self):
        set_calculated_fields(self)
        if self.inv_no:
            frappe.db.set_value("Doc Received", self.inv_no, "rec_details", 1)

    # when delete
    def on_trash(self):
        if self.inv_no:
            frappe.db.set_value("Doc Received", self.inv_no, "rec_details", 0)
