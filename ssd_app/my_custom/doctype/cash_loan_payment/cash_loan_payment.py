# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

def set_currency(doc):
	curr = frappe.db.get_value('Cash Loan', doc.cash_loan_no, 'currency')
	doc.currency = curr

def final_validation(doc):
	pass # need to define


class CashLoanPayment(Document):
	def before_save(self):
		set_currency(self)
