# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
def final_validation(doc):
    if not doc.amount:
        frappe.throw("❌ LC Amount cannot be empty. Please enter the amount.")

class LCOpen(Document):
    def before_save(self):
        if self.amount and self.ex_rate:
            self.amount_usd = round(self.amount / self.ex_rate, 2)
    def validate(self):
	    final_validation(self)
