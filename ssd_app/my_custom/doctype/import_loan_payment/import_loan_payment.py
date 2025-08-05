# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

def set_currency(doc):
	curr = frappe.db.get_value('Import Loan', doc.inv_no, 'currency')
	doc.currency = curr


def final_validation(doc):
	imp_l_amount = frappe.db.get_value("Import Loan", doc.inv_no, "loan_amount") or 0

	# Calculate converted to Import Loan
	imp_l_p_data = frappe.db.sql("""
		SELECT SUM(amount) AS total_imp_l_p
		FROM `tabImport Loan Payment`
		WHERE inv_no = %(inv_no)s AND name != %(name)s
	""", {"inv_no": doc.inv_no, "name": doc.name or ""}, as_dict=True)
	imp_l_p_amount = (imp_l_p_data[0]["total_imp_l_p"] or 0) if imp_l_p_data else 0

	# Check if LC balance is exceeded
	if doc.amount > imp_l_amount - imp_l_p_amount:
		msg = f"""<b>❌ Import Loan Payment Exceeds Import Loan Amount.</b><br>
		<b>Import Loan:</b> {imp_l_amount:,.2f}<br>
		<b>LC Paid:</b> {imp_l_p_amount:,.2f}<br>
		<b>Imp Loan Balance:</b> {(imp_l_amount-imp_l_p_amount):,.2f}<br>
		<b>Entered Amount:</b> {doc.amount:,.2f}
		"""
		frappe.throw(msg)
	


class ImportLoanPayment(Document):
	def before_save(self):
		set_currency(self)

	def validate(self):
		final_validation(self)
	
