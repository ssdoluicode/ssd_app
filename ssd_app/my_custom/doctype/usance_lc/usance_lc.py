# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from ssd_app.utils.banking import check_banking_line

from frappe.utils import getdate, add_days

def set_custom_title(doc):
	if doc.inv_no:
		doc.custom_title = f"{doc.name} ({doc.inv_no.strip()})".strip()


def calculate_due_date(doc):
    if not doc.due_date and doc.term_days:
        bl_date = frappe.db.get_value("CIF Sheet",{"inv_no": doc.inv_no},"inv_date")

        if bl_date:
            bl_date = getdate(bl_date)
            doc.inv_date= bl_date
            doc.due_date = add_days(bl_date, int(doc.term_days))
        else:
            if (doc.inv_date):
                bl_date= doc.inv_date
                doc.due_date = add_days(bl_date, int(doc.term_days))
            else:
                frappe.throw("Please Fill Inv Date")

def calculate_usance_lc_amount_usd(doc):
    if doc.usance_lc_amount and doc.ex_rate:
        doc.usance_lc_amount_usd = round(float(doc.usance_lc_amount) / float(doc.ex_rate), 2)


# def set_company(doc):
# 	if doc.inv_no:
# 		com_num_code= doc.inv_no[0]
# 		company_id = frappe.db.get_value("Company", {"number_code":int(com_num_code)}, "name") or 0
# 		doc.company= company_id
          
# 	else:
# 		frappe.throw("Please Fill Company Name")

def set_company(doc):
    if doc.inv_no:
        com_num_code = doc.inv_no[0]

        # Validate numeric company code
        if not com_num_code.isdigit():
            frappe.throw(f"Invalid company code '{com_num_code}' in Invoice No.")

        # Fetch company by number_code
        company_id = frappe.db.get_value(
            "Company",
            {"number_code": int(com_num_code)},
            "name"
        )

        if not company_id:
            frappe.throw(f"No Company found for number_code: {com_num_code}")

        # Set company
        doc.company = company_id

    else:
        frappe.throw("Please Fill Company Name")



def bank_line_validtation(doc):
    if not doc.usance_lc_amount:
        frappe.throw("❌ Usance LC Amount cannot be empty. Please enter the amount.")

    company_code = frappe.db.get_value("Company", doc.company, "company_code") or ""
    company_code = company_code.replace('.', '').replace('-', '').replace(' ', '_') or ""

    bank_details = frappe.db.get_value("Bank", doc.bank, "bank") or ""
    bank_details = bank_details.replace('.', '').replace('-', '').replace(' ', '_') or ""
    bl = check_banking_line(company_code, bank_details, "lc")

    if bl is None:
        frappe.throw(f"❌ In {company_code} {bank_details} Bank — No banking line found")

    current_ulc = 0
    if not doc.is_new():
        current_ulc = frappe.db.get_value("Usance LC", doc.name, "usance_lc_amount_usd") or 0

    allowed_limit = bl + current_ulc

    if doc.usance_lc_amount_usd > allowed_limit:
        frappe.throw(f"""
            ❌ <b>Usance LC amount exceeds Bank Line Limit!</b><br><br>
            <b>Banking Line Balance:</b> {allowed_limit:,.2f}<br>
            <b>You are trying to enter:</b> {doc.usance_lc_amount_usd:,.2f}
        """)

class UsanceLC(Document):

    def before_save(self):
        set_custom_title(self)
        calculate_due_date(self)

    def validate(self):
        set_company(self)
        calculate_usance_lc_amount_usd(self)
        bank_line_validtation(self)



