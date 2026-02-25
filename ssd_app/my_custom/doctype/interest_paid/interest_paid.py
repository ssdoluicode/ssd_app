# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


def set_calculated_fields(doc):
    invoice, shi_id = frappe.db.get_value(
        "Doc Nego",
        doc.inv_no,
        ["invoice_no", "inv_no"]
    )
    doc.invoice_no = invoice
    doc.custom_title = f"{doc.name} ({invoice})"
    doc.shipping_id = shi_id
    print(shi_id)

class InterestPaid(Document):
    def before_save(self):
        set_calculated_fields(self)
    def validate(self):
          if self.interest is not None and self.interest <= 0:
            frappe.throw("Nothing interest here, Please check.")

