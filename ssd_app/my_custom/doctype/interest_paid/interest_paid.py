# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class InterestPaid(Document):
	def validate(self):
          if self.interest is not None and self.interest <= 0:
            frappe.throw("Nothing interest here, Please check.")


@frappe.whitelist()
def get_nego_data(inv_no, date, name=None):
    # Get main Doc Nego record
    doc = frappe.get_doc("Doc Nego", inv_no)
    nego_amount = doc.nego_amount

    # Get interest_upto_date from related Doc Nego Details
    nego_interest_upto = frappe.db.get_value("Doc Nego Details", {"inv_no": inv_no}, "interest_upto_date")

    # Get all interest_upto_date from Interest Paid except the current record
    int_interest_upto = frappe.db.get_all("Interest Paid",{"inv_no": inv_no, "name": ["!=", name]},pluck="interest_upto_date")

    # Combine both dates
    if nego_interest_upto:
        int_interest_upto.append(nego_interest_upto)

    # Calculate max date safely
    last_interest_upto = max(int_interest_upto) if int_interest_upto else None

    # Get sum of Doc Received amounts before given date
    all_doc_rec = frappe.db.get_all("Doc Received",{"inv_no": doc.inv_no, "received_date": ["<", date]},pluck="received")

    # Get sum of Doc Refund amounts before given date
    all_doc_refund = frappe.db.get_all("Doc Refund",{"inv_no": doc.inv_no, "refund_date": ["<", date]},pluck="refund_amount")

    doc_rec = sum(all_doc_rec) if all_doc_rec else 0
    doc_refund = sum(all_doc_refund) if all_doc_refund else 0

    # Calculate negotiation balance (avoid negative values)
    nego_bal = max(nego_amount - max(doc_rec, doc_refund), 0)

    return {
        "nego_amount": nego_bal,
        "last_interest_upto": last_interest_upto,
    }
