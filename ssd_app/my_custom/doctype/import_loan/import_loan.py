# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from ssd_app.utils.banking import check_banking_line
from datetime import datetime, timedelta



def set_custom_title(doc):
	if doc.inv_no:
		doc.custom_title = f"{doc.name}({doc.inv_no.strip()})"


def calculate_due_date(doc):
	if doc.term_days: 
		if isinstance(doc.loan_date, str): 
			loan_date = datetime.strptime(doc.loan_date, "%Y-%m-%d").date() 
		else: loan_date = doc.loan_date 
		doc.due_date = loan_date + timedelta(days=int(doc.term_days))


def calculate_loan_amount_usd(doc):
    if doc.loan_amount and doc.ex_rate:
        doc.loan_amount_usd = round(float(doc.loan_amount) / float(doc.ex_rate), 2)

def set_company(doc):
	if doc.inv_no:
		com_num_code= doc.inv_no[0]
		company_id = frappe.db.get_value("Company", {"number_code":int(com_num_code)}, "name") or 0
		doc.company= company_id
	else:
		frappe.throw("Please Fill Company Name")
		

def bank_line_validtation(doc):
    if not doc.loan_amount:
        frappe.throw("❌ Loan Amount cannot be empty. Please enter the amount.")

    company_code = frappe.db.get_value("Company", doc.company, "company_code") or ""
    company_code = company_code.replace('.', '').replace('-', '').replace(' ', '_')

    bank_details = frappe.db.get_value("Bank", doc.bank, "bank") or ""
    bank_details = bank_details.replace('.', '').replace('-', '').replace(' ', '_')

    bl = check_banking_line(company_code, bank_details, "imp_l")

    if bl is None:
        frappe.throw(f"❌ In {company_code} {bank_details} Bank — No banking line found")

    current_iln = 0
    if not doc.is_new():
        current_iln = frappe.db.get_value("Import Loan", doc.name, "loan_amount_usd") or 0

    allowed_limit = bl + current_iln

    if doc.loan_amount_usd > allowed_limit:
        frappe.throw(f"""
            ❌ <b>Loan amount exceeds Bank Line Limit!</b><br><br>
            <b>Banking Line Balance:</b> {allowed_limit:,.2f}<br>
            <b>You are trying to enter:</b> {doc.loan_amount_usd:,.2f}
        """)


class ImportLoan(Document):

	def before_save(self):
		set_custom_title(self)
		calculate_due_date(self)

	def validate(self):
		set_company(self)
		calculate_loan_amount_usd(self)
		bank_line_validtation(self)
