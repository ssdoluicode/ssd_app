# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
def set_default(doc):
    if not doc.code:
        doc.code = doc.customer

class Customer(Document):
	def before_save(self):
		set_default(self)
