# Copyright (c) 2026, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class BankNameinTally(Document):
	def validate(self):
		self.validate_at_least_one_company_field()
		
	def validate_at_least_one_company_field(self):
		# Array of your actual database field names
		company_fields = [
			"company_2_bank", "company_8_bank",
			"company_2_nego",  "company_8_nego",
			"company_3_bank", "company_9_bank",
			"company_3_nego",  "company_9_nego"
		]

		if all(not self.get(field) for field in company_fields):
			frappe.throw(_("Validation Form Error: At least one Company field must be filled."))

