# # Copyright (c) 2026, SSDolui and contributors
# # For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ShippingBook(Document):
	pass


@frappe.whitelist()
def check_related_docs(inv_id):
    return bool(frappe.db.exists("Doc Received", {"inv_no": inv_id}) or 
                frappe.db.exists("Doc Nego", {"inv_no": inv_id}))