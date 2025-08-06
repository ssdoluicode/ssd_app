# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

def set_currency(doc):
	curr = frappe.db.get_value('Cash Loan', doc.cash_loan_no, 'currency')
	doc.currency = curr

def final_validation(doc):
	cash_l_amount = frappe.db.get_value("Cash Loan", doc.cash_loan_no, "cash_loan_amount") or 0

	# Calculate converted to Import Loan
	cash_l_p_data = frappe.db.sql("""
		SELECT SUM(amount) AS total_cash_l_p
		FROM `tabCash Loan Payment`
		WHERE cash_loan_no = %(cash_loan_no)s AND name != %(name)s
	""", {"cash_loan_no": doc.cash_loan_no, "name": doc.name or ""}, as_dict=True)
	imp_l_p_amount = (cash_l_p_data[0]["total_cash_l_p"] or 0) if cash_l_p_data else 0

	# Check if LC balance is exceeded
	if doc.amount > cash_l_amount - imp_l_p_amount:
		msg = f"""<b>❌ Cash Loan Payment Exceeds Cash Loan Amount.</b><br>
		<b>Cash Loan:</b> {cash_l_amount:,.2f}<br>
		<b>Cash Loan Paid:</b> {imp_l_p_amount:,.2f}<br>
		<b>Cash Loan Balance:</b> {(cash_l_amount-imp_l_p_amount):,.2f}<br>
		<b>Entered Amount:</b> {doc.amount:,.2f}
		"""
		frappe.throw(msg)
	if not doc.amount:
		frappe.throw("❌ Amount cannot be empty. Please enter the amount.")

class CashLoanPayment(Document):
	def before_save(self):
		set_currency(self)
	def validate(self):
		final_validation(self)