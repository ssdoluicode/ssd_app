# # Copyright (c) 2026, SSDolui and contributors
# # For license information, please see license.txt

import frappe
from frappe.model.document import Document


def validate_inv_no (doc):
    if not doc.inv_no:
        return
    dublicate= frappe.db.exists(
        "Shipping Book",
        {
            "inv_no":doc.inv_no,
            "name":["!=", doc.name]
        }
    )
    if dublicate:
        frappe.throw(
            f"Invoice No {doc.inv_no} already exits in Shipping Book"
        )

class ShippingBook(Document):
    def validate(self):
        validate_inv_no(self)


@frappe.whitelist()
def check_related_docs(inv_id):
    return bool(frappe.db.exists("Doc Received", {"inv_no": inv_id}) or 
                frappe.db.exists("Doc Nego", {"inv_no": inv_id}) or 
                frappe.db.exists("CIF Sheet", {"inv_no": inv_id})) 