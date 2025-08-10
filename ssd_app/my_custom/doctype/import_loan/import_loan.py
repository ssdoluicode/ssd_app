# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

def set_custom_title(doc):
	if doc.lc_no and doc.inv_no:
		lc_no = frappe.db.get_value('LC Open', doc.lc_no, 'lc_no') or ''
		doc.custom_title = f"{lc_no.strip()} :: {doc.inv_no.strip()}"

def set_currency(doc):
	if doc.lc_no:
		doc.currency = frappe.db.get_value('LC Open', doc.lc_no, 'currency') or ''

def final_validation(doc):
	# Fetch LC Open amount and tolerance
	lc_amount = frappe.db.get_value("LC Open", doc.lc_no, "amount") or 0
	tolerance = frappe.db.get_value("LC Open", doc.lc_no, "tolerance") or 0
	max_lc_amount = lc_amount * (100 + tolerance) / 100

	# Total LC Paid
	lc_paid = frappe.db.sql("""
		SELECT SUM(amount) AS total
		FROM `tabLC Payment`
		WHERE lc_no = %(lc_no)s
	""", {"lc_no": doc.lc_no}, as_dict=True)[0].total or 0

	# Total Import Loans (excluding this doc)
	imp_loan = frappe.db.sql("""
		SELECT SUM(loan_amount) AS total
		FROM `tabImport Loan`
		WHERE lc_no = %(lc_no)s AND name != %(name)s
	""", {"lc_no": doc.lc_no, "name": doc.name or ""}, as_dict=True)[0].total or 0

	# Total Usance LC
	usance = frappe.db.sql("""
		SELECT SUM(usance_lc_amount) AS total
		FROM `tabUsance LC`
		WHERE lc_no = %(lc_no)s
	""", {"lc_no": doc.lc_no}, as_dict=True)[0].total or 0

	# Available LC balance
	available = max_lc_amount - lc_paid - imp_loan - usance

	# Validation checks
	if doc.loan_amount == 0:
		frappe.throw("⚠️ <b>Validation Error:</b> Loan Amount cannot be zero.")

	if doc.loan_amount > available:
		msg = f"""
			<b>❌ LC Payment Exceeds LC Balance.</b><br>
			<b>LC Open:</b> {lc_amount:,.2f}<br>
			<b>LC Paid:</b> {lc_paid:,.2f}<br>
			<b>Converted to Import Loan:</b> {imp_loan:,.2f}<br>
			<b>Converted to Usance LC:</b> {usance:,.2f}<br>
			<b>Tolerance ({tolerance}%):</b> {(lc_amount * tolerance / 100):,.2f}<br>
			<b>LC Balance:</b> {available:,.2f}<br>
			<b>Entered Amount:</b> {doc.loan_amount:,.2f}
		"""
		frappe.throw(msg)

class ImportLoan(Document):
	def before_save(self):
		set_currency(self)
		set_custom_title(self)

	def validate(self):
		final_validation(self)
