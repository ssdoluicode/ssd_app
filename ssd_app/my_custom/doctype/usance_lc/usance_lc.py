# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from ssd_app.utils.banking import check_banking_line

from frappe.utils import getdate, add_days

def set_custom_title(doc):
	lc_no = frappe.db.get_value('LC Open', doc.lc_no, 'lc_no')

	# Strip and combine
	doc.custom_title = f"{lc_no.strip()} :: {doc.inv_no.strip()}".strip()
	# doc.title = doc.custom_title

def set_currency(doc):
	curr = frappe.db.get_value('LC Open', doc.lc_no, 'currency')
	doc.currency = curr

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

def final_validation(doc):
	# Get LC Open amount and tolerance
	lc_amount = frappe.db.get_value("LC Open", doc.lc_no, "amount") or 0
	tolerance = frappe.db.get_value("LC Open", doc.lc_no, "tolerance") or 0
	max_lc_amount = lc_amount * (100 + tolerance) / 100

	# Calculate total LC paid amount (excluding this doc)
	lc_p_data = frappe.db.sql("""
		SELECT SUM(amount) AS total_lc_paid
		FROM `tabLC Payment`
		WHERE lc_no = %(lc_no)s AND name != %(name)s
	""", {
		"lc_no": doc.lc_no,
		"name": doc.name or ""
	}, as_dict=True)
	lc_paid_amount = (lc_p_data[0]["total_lc_paid"] or 0) if lc_p_data else 0

	# Calculate converted to Import Loan
	imp_l_data = frappe.db.sql("""
		SELECT SUM(loan_amount) AS total_imp_l
		FROM `tabImport Loan`
		WHERE lc_no = %(lc_no)s
	""", {"lc_no": doc.lc_no}, as_dict=True)
	imp_l_amount = (imp_l_data[0]["total_imp_l"] or 0) if imp_l_data else 0

	# Calculate converted to Usance LC
	usance_lc_data = frappe.db.sql("""
		SELECT SUM(usance_lc_amount) AS total_usance_lc
		FROM `tabUsance LC`
		WHERE lc_no = %(lc_no)s
	""", {"lc_no": doc.lc_no}, as_dict=True)
	u_lc_amount = (usance_lc_data[0]["total_usance_lc"] or 0) if usance_lc_data else 0

	# Check if LC balance is exceeded
	if not doc.is_new():  # need to add logic here
		actual_u_lc = frappe.db.get_value("Usance LC", doc.name, "usance_lc_amount")
		if doc.usance_lc_amount > max_lc_amount - lc_paid_amount - imp_l_amount - u_lc_amount + actual_u_lc:
			msg = f"""<b>❌❌ LC Payment Exceeds LC Balance.</b><br>
			<b>LC Open:</b> {lc_amount:,.2f}<br>"""
			if lc_paid_amount:
				msg += f"<b>LC Paid:</b> {lc_paid_amount:,.2f}<br>"
			if imp_l_amount:
				msg += f"<b>Convert to Import Loan:</b> {imp_l_amount:,.2f}<br>"
			if u_lc_amount:
				msg += f"<b>Convert to Usance LC:</b> {u_lc_amount:,.2f}<br>"
			if tolerance:
				msg += f"<b>Tolerance ({tolerance}%):</b> {(lc_amount * tolerance / 100):,.2f}<br>"

			available = max_lc_amount - lc_paid_amount - imp_l_amount - u_lc_amount
			msg += f"<b>LC Balance:</b> {available:,.2f}<br>"
			msg += f"<b>Entered Amount:</b> {doc.usance_lc_amount:,.2f}<br>"

			frappe.throw(msg)



	elif doc.usance_lc_amount > max_lc_amount - lc_paid_amount - imp_l_amount - u_lc_amount:
		msg = f"""<b>❌ LC Payment Exceeds LC Balance.</b><br>
		<b>LC Open:</b> {lc_amount:,.2f}<br>"""
		if lc_paid_amount:
			msg += f"<b>LC Paid:</b> {lc_paid_amount:,.2f}<br>"
		if imp_l_amount:
			msg += f"<b>Convert to Import Loan:</b> {imp_l_amount:,.2f}<br>"
		if u_lc_amount:
			msg += f"<b>Convert to Usance LC:</b> {u_lc_amount:,.2f}<br>"
		if tolerance:
			msg += f"<b>Tolerance ({tolerance}%):</b> {(lc_amount * tolerance / 100):,.2f}<br>"

		available = max_lc_amount - lc_paid_amount - imp_l_amount - u_lc_amount
		msg += f"<b>LC Balance:</b> {available:,.2f}<br>"
		msg += f"<b>Entered Amount:</b> {doc.usance_lc_amount:,.2f}<br>"

		frappe.throw(msg)
	if doc.usance_lc_amount == 0:
		frappe.throw("⚠️ <b>Validation Error:</b> Please enter a valid Usance LC Amount. It cannot be zero.")

class UsanceLC(Document):
	def validate(self):
		calculate_due_date(self)
		final_validation(self)
	
	def before_save(self):
		set_currency(self)
		if self.lc_no and self.inv_no:
			set_custom_title(self)
