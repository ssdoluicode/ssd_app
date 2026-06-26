# Copyright (c) 2026, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document 
from frappe import _


class CustomerTallyName(Document):
	def validate(self):
		self.validate_at_least_one_company_field()
		
	def validate_at_least_one_company_field(self):
		# Array of your actual database field names
		company_fields = [
			"company_2_doc", "company_8_doc",
			"company_2_cc",  "company_8_cc",
			"company_3_doc", "company_9_doc",
			"company_3_cc",  "company_9_cc"
		]

		if all(not self.get(field) for field in company_fields):
			frappe.throw(_("Validation Form Error: At least one Company field must be filled."))

