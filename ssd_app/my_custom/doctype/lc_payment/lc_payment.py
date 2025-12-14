
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
	group_id= f"{doc.company} : {doc.bank}"
	# Banking line
	bl = frappe.db.sql("""
            SELECT
                SUM(lc_o.amount_usd)
                - IFNULL(lc_p.lc_p_amount, 0)
                - IFNULL(imp_ln.to_imp_ln, 0)
                - IFNULL(usance_lc.to_usance_lc, 0)
            FROM `tabLC Open` lc_o
            LEFT JOIN (
                SELECT group_id, SUM(amount_usd) AS lc_p_amount
                FROM `tabLC Payment`
                GROUP BY group_id
            ) lc_p ON lc_p.group_id = lc_o.group_id
            LEFT JOIN (
                SELECT group_id, SUM(loan_amount_usd) AS to_imp_ln
                FROM `tabImport Loan`
                WHERE from_lc_open = 1
                GROUP BY group_id
            ) imp_ln ON imp_ln.group_id = lc_o.group_id
            LEFT JOIN (
                SELECT group_id, SUM(usance_lc_amount_usd) AS to_usance_lc
                FROM `tabUsance LC`
                WHERE from_lc_open = 1
                GROUP BY group_id
            ) usance_lc ON usance_lc.group_id = lc_o.group_id
            WHERE lc_o.group_id = %s
        """, group_id)[0][0] or 0.0

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
	def validate(self):
		final_validation(self)

	def before_save(self):
		if self.company and self.bank:
			self.group_id = f"{self.company} : {self.bank}"
