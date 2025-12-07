# # Copyright (c) 2025, SSDolui and contributors
# # For license information, please see license.txt

# import frappe
# from frappe.model.document import Document
# from ssd_app.utils.banking import check_banking_line


# def final_validation(doc):
# 	if doc.amount == 0:
# 		frappe.throw("⚠️ <b>Validation Error:</b> Please enter a valid Amount. It cannot be zero.")
	
# 	company_code = frappe.db.get_value("Company", doc.company, "company_code")
# 	company_code=company_code.replace('.', '').replace('-', '').replace(' ', '_')
# 	bank_details = frappe.db.get_value("Bank", doc.bank, "bank")
# 	bank_details=bank_details.replace('.', '').replace('-', '').replace(' ', '_')
# 	bl = check_banking_line(company_code, bank_details, "lc") or 0
# 	bl = float(bl)

# 	if bl == 0:
# 		frappe.throw("❌ No banking Line")

# 	if not doc.is_new():  
# 		actual_lc_paid = frappe.db.get_value("LC Paid", doc.name, "amount")
# 		frappe.msgprint(actual_lc_paid)
		
# 		if doc.amount  > (bl + actual_lc_paid):
# 			frappe.throw(f"""
#                 ❌ <b>Nego amount exceeds Bank Line Limit.</b><br>
#                 <b>Banking Line Balance:</b> {bl + actual_lc_paid:,.2f}<br>
#                 <b>Try to Entry:</b> {doc.amount :,.2f}<br>
#             """)
# 		elif doc.amount > bl:
# 			frappe.throw((f"""
# 			❌ <b>LC amount exceeds Bank Line Limit.</b><br>
# 			<b>Banking Line Balance:</b> {bl:,.2f}<br>
# 			<b>Try to Entry:</b> {doc.amount :,.2f}<br>
# 		"""))



# class LCPayment(Document):
# 	def before_save(self):
# 		if self.company and self.bank:
# 			self.group_id = f"{self.company} : {self.bank}"
# 	def validate(self):
# 		final_validation(self)


# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from ssd_app.utils.banking import check_banking_line


def final_validation(doc):

	# Validate amount
	if doc.amount == 0:
		frappe.throw("⚠️ <b>Validation Error:</b> Please enter a valid Amount. It cannot be zero.")

	# Company code cleanup
	company_code = frappe.db.get_value("Company", doc.company, "company_code")
	company_code = company_code.replace('.', '').replace('-', '').replace(' ', '_')

	# Bank details cleanup
	bank_details = frappe.db.get_value("Bank", doc.bank, "bank")
	bank_details = bank_details.replace('.', '').replace('-', '').replace(' ', '_')

	# Banking line
	bl = check_banking_line(company_code, bank_details, "lc") or 0
	bl = float(bl)

	if bl <= 0:
		frappe.throw("❌ No Banking Line available for this Company & Bank")

	# Validation for existing documents
	if not doc.is_new():
		actual_lc_paid = frappe.db.get_value("LC Paid", doc.name, "amount") or 0
		actual_lc_paid = float(actual_lc_paid)


		# Total Available = Banking Line + Already Paid
		total_available = bl + actual_lc_paid

		if doc.amount > total_available:
			frappe.throw(f"""
				❌ <b>Nego amount exceeds Bank Line Limit.</b><br>
				<b>Banking Line Balance:</b> {total_available:,.2f}<br>
				<b>Try to Entry:</b> {doc.amount:,.2f}<br>
			""")

		elif doc.amount > bl:
			frappe.throw(f"""
				❌ <b>LC amount exceeds Bank Line Limit.</b><br>
				<b>Banking Line Balance:</b> {bl:,.2f}<br>
				<b>Try to Entry:</b> {doc.amount:,.2f}<br>
			""")


class LCPayment(Document):

	def before_save(self):
		if self.company and self.bank:
			self.group_id = f"{self.company} : {self.bank}"

	def validate(self):
		final_validation(self)
