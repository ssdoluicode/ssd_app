# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CashLoan(Document):
	def before_save(self):
		if self.cash_loan_amount and self.ex_rate:
			self.cash_loan_amount_usd = round(self.cash_loan_amount / self.ex_rate, 2)
