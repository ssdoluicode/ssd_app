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
        FROM `tabImport Loan Payment`
        WHERE (import_loan_payment_details != 1 OR import_loan_payment_details IS NULL)
        AND name LIKE %s
        ORDER BY name ASC
        LIMIT %s OFFSET %s
    """, values)


@frappe.whitelist()
def get_imp_loan_data(import_loan_id):
    payment_data = frappe.db.get_value("Import Loan Payment", import_loan_id, 
        ["amount", "payment_date", "currency", "inv_no"], as_dict=True)

    if not payment_data:
        return {}
    loan_info = frappe.db.get_value("Import Loan", payment_data.inv_no, 
        ["name", "bank", "company", "loan_date", "loan_amount", "inv_no"], as_dict=True)
    loan_details = frappe.db.get_value("Import Loan Details", {"import_loan_id":loan_info.name}, ["interest_pct"], as_dict=True)
    interest_pct = loan_details.interest_pct if loan_details else 0

    # 1. Fetch the data
    previous_payments = frappe.db.get_all("Import Loan Payment Details",
        filters={
            "loan_id": payment_data.inv_no,
            "name": ["!=", import_loan_id],
            "payment_date": ["<=", payment_data.payment_date]
        },
        fields=["SUM(payment_amount) as total_paid", "SUM(accrued_interest) AS prev_accrued_interest", "MAX(interest_upto) AS interest_from"]
    )
    
    # Safe extraction logic
    row = (previous_payments or [{}])[0]
    total_prev_paid = row.get("total_paid") or 0
    prev_accrued_interest = row.get("prev_accrued_interest") or 0
    interest_from= row.get("interest_from") or loan_info.loan_date

    bank_name = frappe.db.get_value("Bank", loan_info.bank, "bank") if loan_info else None
    com_code = frappe.db.get_value("Company", loan_info.company, "company_code") if loan_info else None
    
    return {
        "amount": payment_data.amount,
        "date": payment_data.payment_date,
        "com": com_code,
        "bank_name": bank_name,
        "currency": payment_data.currency,
        "interest_from":interest_from,
        "interest_pct": interest_pct,
        "interest_on" : loan_info.loan_amount- total_prev_paid,
        "inv_no":loan_info.inv_no,
        "prev_accrued_interest": prev_accrued_interest,
        "loan_id": payment_data.inv_no
    }


class ImportLoanPaymentDetails(Document):
	pass
