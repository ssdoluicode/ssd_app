# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

@frappe.whitelist()
def get_available_id(doctype, txt, searchfield, start, page_len, filters):

    txt = f"%{txt}%"
    values = (txt, page_len, start)

    return frappe.db.sql("""
		SELECT
			name
		FROM `tabCC Received`
		WHERE (cc_received_details != 1 OR cc_received_details IS NULL)
		AND entry_type = 'Bank Entry'
		AND name LIKE %s
		ORDER BY name ASC
		LIMIT %s OFFSET %s
	""", values)

@frappe.whitelist()
def get_cc_rec_data(name):
    doc = frappe.get_doc("CC Received", name)
	
    
    customer = frappe.db.get_value("Customer", doc.customer, "customer")
    
    # Return only the required fields
    return {
        "customer": customer,
        "date": doc.date,
        "amount": doc.amount,
        "currency": doc.currency
    }


class CCReceivedDetails(Document):
	# when create/update
    def before_save(self):
        if self.cc_received_id:
            frappe.db.set_value("CC Received", self.cc_received_id, "cc_received_details", 1)

    # when delete
    def on_trash(self):
        if self.cc_received_id:
            frappe.db.set_value("CC Received", self.cc_received_id, "cc_received_details", 0)

