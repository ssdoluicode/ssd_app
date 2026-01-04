# Copyright (c) 2026, SSDolui and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class BankBankingLine(Document):
	def validate(self):
		if self.banking_line_name:
			self.custom_title = f"{self.name} :: {self.banking_line_name}"

