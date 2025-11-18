# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from ssd_app.utils.banking import check_banking_line
from datetime import datetime, timedelta


def set_custom_title(doc):
	if doc.inv_no:
		doc.custom_title = f"{doc.name}({doc.inv_no.strip()})"

# def set_currency(doc): #working
# 	if doc.lc_no:
# 		doc.currency = frappe.db.get_value('LC Open', doc.lc_no, 'currency') or ''

def calculate_due_date(doc):
	if doc.term_days: 
		if isinstance(doc.loan_date, str): 
			loan_date = datetime.strptime(doc.loan_date, "%Y-%m-%d").date() 
		else: loan_date = doc.loan_date 
		doc.due_date = loan_date + timedelta(days=int(doc.term_days))


def calculate_loan_amount_usd(doc):
    if doc.loan_amount and doc.ex_rate:
        doc.loan_amount_usd = round(float(doc.loan_amount) / float(doc.ex_rate), 2)


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


def bank_line_validtation(doc):
    if not doc.loan_amount:
        frappe.throw("❌ Loan Amount cannot be empty. Please enter the amount.")

    company_code = frappe.db.get_value("Company", doc.company, "company_code")
    company_code=company_code.replace('.', '').replace('-', '').replace(' ', '_')
    bank_details = frappe.db.get_value("Bank", doc.bank, "bank")
    bank_details=bank_details.replace('.', '').replace('-', '').replace(' ', '_')
    frappe.msgprint(bank_details)
    bl = check_banking_line(company_code, bank_details, "imp_l")
    # ex_rate = frappe.db.get_value('LC Open', doc.lc_no, 'ex_rate')
    # frappe.msgprint(str(bl))
    if bl == None:
        frappe.throw(f"❌ In {company_code} {bank_details} Bank No banking Line")

    elif doc.loan_amount_usd  > bl:
        frappe.throw((f"""
        ❌ <b>Loan amount exceeds Bank Line Limit.</b><br>
        <b>Banking Line Balance:</b> {bl:,.2f}<br>
        <b>Try to Entry:</b> {doc.loan_amount_usd:,.2f}<br>
    """))

class ImportLoan(Document):

	def before_save(self):
		# set_currency(self) working
		set_custom_title(self)
		calculate_due_date(self)
		calculate_loan_amount_usd(self)

	def validate(self):
		# final_validation(self)
		calculate_loan_amount_usd(self)
		bank_line_validtation(self)
