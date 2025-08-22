# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from ssd_app.utils.banking import check_banking_line

def bank_line_validtation(doc):
    if not doc.cash_loan_amount:
        frappe.throw("❌ Loan Amount cannot be empty. Please enter the amount.")

    company_code = frappe.db.get_value("Company", doc.company, "company_code")
    company_code=company_code.replace('.', '').replace('-', '').replace(' ', '_')
    bank_details = frappe.db.get_value("Bank", doc.bank, "bank")
    bank_details=bank_details.replace('.', '').replace('-', '').replace(' ', '_')
    bl = check_banking_line(company_code, bank_details, "c_loan")
    if bl == None:
        frappe.throw("❌ No banking Line")

    elif (doc.cash_loan_amount / doc.ex_rate) > bl:
        frappe.throw((f"""
        ❌ <b>Loan amount exceeds Bank Line Limit.</b><br>
        <b>Banking Line Balance:</b> {bl:,.2f}<br>
        <b>Try to Entry:</b> {(doc.cash_loan_amount / doc.ex_rate):,.2f}<br>
    """))



class CashLoan(Document):
	def before_save(self):
		if self.cash_loan_amount and self.ex_rate:
			self.cash_loan_amount_usd = round(self.cash_loan_amount / self.ex_rate, 2)
	def validate(self):
		bank_line_validtation(self)
