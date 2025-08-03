# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

def final_validation(doc):
	u_lc_amount = frappe.db.get_value("Usance LC", doc.inv_no, "usance_lc_amount") or 0

	# Calculate converted to Import Loan
	u_lc_p_data = frappe.db.sql("""
		SELECT SUM(amount) AS total_u_lc_p
		FROM `tabUsance LC Payment`
		WHERE inv_no = %(inv_no)s AND name != %(name)s
	""", {"inv_no": doc.inv_no, "name": doc.name or ""}, as_dict=True)
	u_lc_p_amount = (u_lc_p_data[0]["total_u_lc_p"] or 0) if u_lc_p_data else 0

	# Check if LC balance is exceeded
	if doc.amount > u_lc_amount - u_lc_p_amount:
		msg = f"""<b>❌ Usance LC Payment Exceeds Usance LC Amount.</b><br>
		<b>Usance LC:</b> {u_lc_amount:,.2f}<br>
		<b>Usance LC Paid:</b> {u_lc_p_amount:,.2f}<br>
		<b>Imp Loan Balance:</b> {(u_lc_amount-u_lc_p_amount):,.2f}<br>
		<b>Entered Amount:</b> {doc.amount:,.2f}
		"""
		frappe.throw(msg)
	


class UsanceLCPayment(Document):
	def validate(self):
		final_validation(self)
