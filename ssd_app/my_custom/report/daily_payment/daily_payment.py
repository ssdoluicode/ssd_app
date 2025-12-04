# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt


import frappe
from frappe.utils import today

def execute(filters=None):
	columns = [
		{"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 150},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 150},
		{"label": "Received", "fieldname": "received", "fieldtype": "Float", "width": 110},
		{"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 90}
	]

	data = frappe.db.sql(f"""
		SELECT 
			cif.inv_no AS inv_no, 
            dr.received_date AS date,
			cus.customer AS customer, 
			bank.bank AS bank, 
			dr.received AS received 
		FROM `tabDoc Received` dr
		LEFT JOIN `tabCIF Sheet` cif ON cif.name = dr.inv_no
		LEFT JOIN `tabBank` bank ON bank.name = dr.bank
		LEFT JOIN `tabCustomer` cus ON cus.name = dr.customer
		WHERE DATE(dr.creation) = %s
	""", (today(),), as_dict=1)
	return columns, data

def send_daily_sales_report():
    try:
        # Load the Auto Email Report document
        report = frappe.get_doc("Auto Email Report", "Daily Payment")
        
        # Send it (uses the same logic as clicking "Send Now" in the UI)
        report.send()
        
        # frappe.logger().info("Daily Payment email report sent successfully.")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to send Daily Payment Auto Email Report")