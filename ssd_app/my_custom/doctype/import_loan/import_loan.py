# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from ssd_app.utils.banking import check_banking_line
from ssd_app.utils.banking_line import check_banking_line
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

		

def bank_line_validtation(doc):
    if not doc.loan_amount:
        frappe.throw("❌ Loan Amount cannot be empty. Please enter the amount.")

    company_name = frappe.db.get_value("Company", doc.company, "company_code") or ""
    bank_name = frappe.db.get_value("Bank", doc.bank, "bank") or ""
    group_id= f"{doc.company} : {doc.bank}"

    from_lc_open= int((doc.from_lc_open))
    if from_lc_open ==1:
        lc_term_name= frappe.db.get_value("Payment Term", {"term_name":"LC Open"}, "name")
        lc_bl_data=check_banking_line_n(doc.bank, doc.company,lc_term_name)
        lc_open_line = lc_bl_data["banking_line_name"]

        term_name_2= frappe.db.get_value("Payment Term", {"term_name":"Import Loan"}, "name")
        bl_data_2=check_banking_line_n(doc.bank, doc.company, term_name_2)
        imp_loan_line = bl_data_2["banking_line_name"]
       
        if (lc_open_line == imp_loan_line):
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
        
        else:
              bl= bl_data_2["balance_line"]

    else:
        term_name_2= frappe.db.get_value("Payment Term", {"term_name":"Import Loan"}, "name")
        bl_data_2=check_banking_line(doc.bank, doc.company, term_name_2)
        bl= bl_data_2["balance_line"]

    if bl ==0:
        frappe.throw(f"❌ In {company_name} {bank_name} Bank — No banking line found")

    current_iln = 0
    if not doc.is_new():
        current_iln = frappe.db.get_value("Import Loan", doc.name, "loan_amount_usd") or 0

    allowed_limit = bl + current_iln

    if doc.loan_amount_usd > allowed_limit:
        if from_lc_open ==1:
            frappe.throw(f"""
                ❌ <b> Import Loan amount exceeds the LC Amount</b><br><br>
                <b>Balance LC Open:</b> {allowed_limit:,.2f}<br>
                <b>You are trying to enter:</b> {doc.loan_amount_usd:,.2f}
            """)
        else:
            frappe.throw(f"""
                ❌ <b>Loan amount exceeds Bank Line Limit!</b><br><br>
                <b>Banking Line Balance:</b> {allowed_limit:,.2f}<br>
                <b>You are trying to enter:</b> {doc.loan_amount_usd:,.2f}
            """)


class ImportLoan(Document):

	def before_save(self):
		set_custom_title(self)
		calculate_due_date(self)
		calculate_loan_amount_usd(self)
		if self.company and self.bank:
			self.group_id = f"{self.company} : {self.bank}"

	def validate(self):
		# set_company(self)
		bank_line_validtation(self)

@frappe.whitelist()
def get_supplier(invoice_no):
    inv_id = frappe.get_value("CIF Sheet", {"inv_no":invoice_no}, "name")
    supplier = frappe.db.get_value("Cost Sheet", {"inv_no":inv_id}, "supplier")
    return {"supplier": supplier or None}