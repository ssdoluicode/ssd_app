# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

@frappe.whitelist()
def loan_id_filter(doctype, txt, searchfield, start, page_len, filters):

    txt = f"%{txt}%"
    values = (txt, page_len, start)

    return frappe.db.sql(f"""
        SELECT
            name
        FROM `tabImport Loan`
        WHERE (import_loan_details != 1 OR import_loan_details IS NULL)
        AND name LIKE %s
        ORDER BY name ASC
        LIMIT %s OFFSET %s
    """, values)



@frappe.whitelist()
def get_import_data(import_loan_id):
    doc = frappe.get_doc("Import Loan", import_loan_id)
	
    bank_name = frappe.db.get_value("Bank", doc.bank, "bank")
    com = frappe.db.get_value("Company", doc.company, "company_code")
    supplier = frappe.db.get_value("Supplier", doc.supplier, "supplier")
	
    # Return only the required fields
    return {
        "amount": doc.loan_amount,
        "date": doc.loan_date,
        "com":com,
        "bank_name": bank_name,
        "currency": doc.currency,
        "supplier": supplier,
        "inv_no" : doc.inv_no
    }



class ImportLoanDetails(Document):
    def before_save(self):
        if self.import_loan_id:
            frappe.db.set_value("Import Loan", self.import_loan_id, "import_loan_details", 1)		
    def on_trash(self):
        if self.import_loan_id:
            frappe.db.set_value("Import Loan", self.import_loan_id, "import_loan_details", 0)		

