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


def bank_line_validtation(doc):
    if not doc.usance_lc_amount:
        frappe.throw("❌ Usance LC Amount cannot be empty. Please enter the amount.")

    company_code = frappe.db.get_value("Company", doc.company, "company_code") or ""
    company_code = company_code.replace('.', '').replace('-', '').replace(' ', '_') or ""

    bank_details = frappe.db.get_value("Bank", doc.bank, "bank") or ""
    bank_details = bank_details.replace('.', '').replace('-', '').replace(' ', '_') or ""
    group_id= f"{doc.company} : {doc.bank}"

    from_lc_open= int((doc.from_lc_open))
    if from_lc_open ==1:
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
        bl = check_banking_line(company_code, bank_details, "lc")
    
    if bl is None:
        frappe.throw(f"❌ In {company_code} {bank_details} Bank — No banking line found")

    current_ulc = 0
    if not doc.is_new():
        current_ulc = frappe.db.get_value("Usance LC", doc.name, "usance_lc_amount_usd") or 0

    allowed_limit = bl + current_ulc

    if doc.usance_lc_amount_usd > allowed_limit:
        if from_lc_open == 1:
            frappe.throw(f"""
                ❌ <b>Usance LC amount exceeds LC Open Amount </b><br><br>
                <b>Balance LC Open:</b> {allowed_limit:,.2f}<br>
                <b>You are trying to enter:</b> {doc.usance_lc_amount_usd:,.2f}
            """)
        else:
            frappe.throw(f"""
                ❌ <b>Usance LC amount exceeds Bank Line Limit!</b><br><br>
                <b>Banking Line Balance:</b> {allowed_limit:,.2f}<br>
                <b>You are trying to enter:</b> {doc.usance_lc_amount_usd:,.2f}
            """)


class UsanceLC(Document):
    def validate(self):
        bank_line_validtation(self)

    def before_save(self):
        set_custom_title(self)
        calculate_due_date(self)
        calculate_usance_lc_amount_usd(self)
        if self.company and self.bank:
            self.group_id = f"{self.company} : {self.bank}"

@frappe.whitelist()
def get_supplier(invoice_no):
    # Fetch CIF Sheet record safely
    data = frappe.get_value(
        "CIF Sheet",
        {"inv_no": invoice_no},
        ["name", "inv_date"],
        as_dict=True
    )

    if not data:
        # No matching CIF Sheet
        return {
            "supplier": None,
            "inv_date": ""
        }

    # Fetch Supplier safely
    supplier = frappe.db.get_value("Cost Sheet", {"inv_no": data.name}, "supplier")

    return {
        "supplier": supplier or None,
        "inv_date": data.inv_date or ""
    }
