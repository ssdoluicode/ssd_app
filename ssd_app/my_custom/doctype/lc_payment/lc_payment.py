# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from ssd_app.utils.banking import check_banking_line


def final_validation(doc):
	if doc.amount == 0:
		frappe.throw("⚠️ <b>Validation Error:</b> Please enter a valid Amount. It cannot be zero.")
	
	company_code = frappe.db.get_value("Company", doc.company, "company_code")
	company_code=company_code.replace('.', '').replace('-', '').replace(' ', '_')
	bank_details = frappe.db.get_value("Bank", doc.bank, "bank")
	bank_details=bank_details.replace('.', '').replace('-', '').replace(' ', '_')
	bl = check_banking_line(company_code, bank_details, "lc")

	if bl == None:
		frappe.throw("❌ No banking Line")

	if not doc.is_new():  
		actual_lc_paid = frappe.db.get_value("LC Paid", doc.name, "amount")
		if doc.amount  > (bl + actual_lc_paid):
			frappe.throw(f"""
                ❌ <b>Nego amount exceeds Bank Line Limit.</b><br>
                <b>Banking Line Balance:</b> {bl + actual_lc_paid:,.2f}<br>
                <b>Try to Entry:</b> {doc.amount :,.2f}<br>
            """)
		elif doc.amount > bl:
			frappe.throw((f"""
			❌ <b>LC amount exceeds Bank Line Limit.</b><br>
			<b>Banking Line Balance:</b> {bl:,.2f}<br>
			<b>Try to Entry:</b> {doc.amount :,.2f}<br>
		"""))



class LCPayment(Document):
	def before_save(self):
		if self.company and self.bank:
			self.group_id = f"{self.company} : {self.bank}"
	def validate(self):
		final_validation(self)
