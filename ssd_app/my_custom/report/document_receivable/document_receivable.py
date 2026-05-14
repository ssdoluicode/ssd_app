# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import fmt_money
from datetime import date, timedelta


def get_today_str():
    return date.today().strftime("%Y-%m-%d")

def execute(filters=None):

	p_term=filters.p_term
	if not p_term:
		p_term = frappe.get_all(
			"Payment Term",
			filters={
				"term_type": "Export",
				"use_banking_line": 1
			},
			pluck="name"
		)
	
	bank=filters.bank
	if not bank:
		bank = frappe.get_all(
			"Bank",
			filters={
				"active": 1
			},
			pluck="name"
		)
	conditional_filter = ""
	if filters.based_on == "Receivable":
		conditional_filter = "AND shi.doc_receivable > 0"
	elif filters.based_on == "Coll":
		conditional_filter = """AND shi.doc_collection > 0"""
	elif filters.based_on == "Nego":
		conditional_filter ="""AND shi.doc_nego >0"""
	elif filters.based_on == "Refund":
		# conditional_filter = "AND GREATEST(IFNULL(ref.total_ref, 0) - IFNULL(rec.total_rec, 0), 0) > 0"
		conditional_filter="""AND shi.doc_refund >0"""

	columns = [
		{"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 85},
		{"label": "Inv Date", "fieldname": "bl_date", "fieldtype": "Date", "width": 110},
		{"label": "Com", "fieldname": "com", "fieldtype": "Data", "width": 60},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 120},
		{"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 180},
		{"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 60},
		{"label": "P Term", "fieldname": "p_term", "fieldtype": "Data", "width": 100},
		{"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 115},
		{"label": "Received", "fieldname": "total_rec", "fieldtype": "Float", "width": 115},
		{"label": "Receivable", "fieldname": "receivable", "fieldtype": "Float", "width": 115},
		{"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 110},
		{"label": "Refund Date", "fieldname": "refund_date", "fieldtype": "Date", "width": 110},
		{"label": "Coll", "fieldname": "coll", "fieldtype": "Float", "width": 110},
		{"label": "Nego", "fieldname": "nego", "fieldtype": "Float", "width": 110},
		{"label": "Refund", "fieldname": "refund", "fieldtype": "Float", "width": 110},
	]

	data = frappe.db.sql(f"""
		SELECT shi.inv_no, cif.name AS cif_id,
			shi.name, shi.bl_date, com.company_code AS com, cus.code AS customer, noti.code AS notify, bank.bank,  
					shi.document, shi.doc_received AS total_rec, shi.doc_receivable AS receivable, 
					IF(pt.term_name IN ('LC', 'DA'), CONCAT(pt.term_name, '- ', shi.term_days),pt.term_name) AS p_term, cif.due_date, 
					IF(shi.doc_nego=0, "", nego.refund_date) AS refund_date,
					ROUND(shi.document, 2) AS document, shi.doc_collection AS coll, shi.doc_nego AS nego, shi.doc_refund AS refund,
					CASE WHEN nego.refund_date IS NOT NULL THEN DATEDIFF(nego.refund_date, CURDATE()) END AS days_to_due
					FROM `tabShipping Book` shi 
					LEFT JOIN `tabPayment Term` pt ON shi.payment_term= pt.name
					LEFT JOIN `tabNotify` noti ON noti.name= shi.notify
					LEFT JOIN `tabCustomer` cus ON cus.name= shi.customer
					LEFT JOIN `tabBank` bank ON bank.name= shi.bank
					LEFT JOIN `tabCompany` com ON com.name= shi.company
					LEFT JOIN `tabCIF Sheet` cif ON cif.inv_no= shi.name
					LEFT JOIN (
					  		SELECT inv_no, MIN(bank_due_date) AS refund_date FROM `tabDoc Nego` GROUP BY inv_no
					  		) nego ON nego.inv_no= shi.name
					WHERE shi.document > 0 AND pt.direct_to_supplier = 0 AND pt.full_tt=0 
					{conditional_filter}
					AND shi.payment_term IN %(p_term)s
					AND shi.bank IN %(bank)s
					""", {"p_term":tuple(p_term), "bank":tuple(bank)}, as_dict=1)

	return columns, data


@frappe.whitelist()
def get_doc_flow(inv_name):
	if not inv_name:
		return "Invalid Invoice Number"

	doc = frappe.get_doc("Shipping Book", inv_name)

	customer = frappe.get_value("Customer", doc.customer, "code")
	notify = frappe.get_value("Notify", doc.notify, "code")
	bank = frappe.get_value("Bank", doc.bank, "bank")

	payment_term_data = frappe.db.get_value("Payment Term",doc.payment_term,["term_name", "use_banking_line", "direct_to_supplier"],as_dict=True) or {}

	payment_term = payment_term_data.get("term_name")
	use_banking_line = payment_term_data.get("use_banking_line")
	direct_to_supplier = payment_term_data.get("direct_to_supplier")

	doc_amount = doc.document or 0

	# One query to get all related docs
	entries = frappe.db.sql("""
		SELECT name, 'Nego' AS Type, nego_date AS Date, nego_amount AS Amount, note AS Note FROM `tabDoc Nego` WHERE inv_no=%s
		UNION ALL
		SELECT name, 'Refund', refund_date, refund_amount, note FROM `tabDoc Refund` WHERE inv_no=%s
		UNION ALL
		SELECT name, 'Received', received_date, received, note FROM `tabDoc Received` WHERE inv_no=%s
	""", (inv_name, inv_name, inv_name), as_dict=1)

	# Start with sales
	combined = [{"name": doc.name, "Type": "Sales", "Date": doc.bl_date, "Amount": doc_amount, "Note": ""}] + entries
	combined.sort(key=lambda x: x["Date"] or date.today())

	# Running totals
	coll, nego_amt, refund, received = 0, 0, 0, 0
	rows = []

	for entry in combined:
		typ, amt, note = entry["Type"], entry["Amount"] or 0, entry.get("Note") or ""

		if typ == "Sales":
			coll += amt
		elif typ == "Nego":
			coll -= amt
			nego_amt += amt
		elif typ == "Refund":
			nego_amt -= amt
			refund += amt
		elif typ == "Received":
			remain = amt
			for pool in [('nego_amt', nego_amt), ('refund', refund), ('coll', coll)]:
				if remain <= 0: break
				pool_name, pool_value = pool
				use = min(remain, pool_value)
				remain -= use
				if pool_name == 'nego_amt': nego_amt -= use
				elif pool_name == 'refund': refund -= use
				else: coll -= use
			received += amt

		rows.append(f"""
			<tr>
				<td>{typ}</td>
				<td>{entry['Date']}</td>
				<td style="text-align:right;">{fmt_money(amt)}</td>
				<td style="text-align:right;">{fmt_money(received)}</td>
				<td style="text-align:right;">{fmt_money(doc_amount - received)}</td>
				<td style="text-align:right;background-color:silver;">{fmt_money(coll)}</td>
				<td style="text-align:right;background-color:silver;">{fmt_money(nego_amt)}</td>
				<td style="text-align:right;background-color:silver;">{fmt_money(refund)}</td>
				<td style="text-align:right;">{note}</td>
			</tr>
		""")

	# Build buttons
	
 
	due_date_str = (date.today() + timedelta(days=doc.term_days)).strftime("%Y-%m-%d")
	buttons_html = ""


	
	if round(coll,2) > 0 and use_banking_line:
		buttons_html += f"""
		<a href="#" onclick="frappe.new_doc('Doc Nego', {{ inv_no: '{inv_name}', term_days:'{doc.term_days}', nego_amount: {coll}, bank_due_date:'{due_date_str}' }}); return false;" class="btn btn-primary btn-sm" style="margin-left:8px;background-color:blue;">Nego</a>"""
		
	if round(nego_amt,2) > 0:
		buttons_html += f"""
		<a href="#" onclick="frappe.new_doc('Doc Refund', {{ inv_no: '{inv_name}', refund_date:'{get_today_str()}', refund_amount:'{nego_amt}' }}); return false;" class="btn btn-danger btn-sm" style="margin-left:8px;background-color:red;">Refund</a>"""
	if (round((doc_amount - received),2) > 0 and direct_to_supplier==0):
		buttons_html += f"""
		<a href="#" onclick="frappe.new_doc('Doc Received', {{ inv_no: '{inv_name}', received_date:'{get_today_str()}', received:'{doc_amount - received}' }}); return false;" class="btn btn-success btn-sm" style="margin-left:8px;background-color:green;">Received</a>"""



	# Build final HTML
	html = f"""
	<div style="bmargin-bottom: 12px; background-color: #f9f9f9; padding: 8px 12px;  border-radius: 6px; 
	box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
    <table style="width:100%; font-size:13px; margin-bottom:0;">
			<tr><td><b>Invoice Date:</b> {doc.bl_date}</td><td><b>Customer:</b> {customer}</td><td><b>Notify:</b> {notify}</td></tr>
			<tr><td><b>Bank:</b> {bank}</td><td><b>Payment Term:</b> {payment_term}{' - '+str(doc.term_days) if payment_term in ['LC','DA'] else ''}</td></tr>
		</table>
	</div>
	<table class="table table-bordered" style="font-size:14px; border:1px solid #ddd;">
		<thead style="background-color: #f1f1f1;">
			<tr>
				<th style="width:10%; text-align:center;">Type</th>
				<th style="width:15%; text-align:center;">Date</th>
				<th style="width:10%;text-align:center;">Amount</th>
				<th style="width:10%;text-align:center;">Received</th>
				<th style="width:10%;text-align:center;">Receivable</th>
				<th style="width:10%;text-align:center;">Coll</th>
				<th style="width:10%;text-align:center;">Nego</th>
				<th style="width:10%;text-align:center;">Refund</th>
				<th style="width:15%;text-align:center;">Note</th>
			</tr>
		</thead>
		<tbody style="border-top:1px solid #ddd;">

			{''.join(rows)}
		</tbody>
	</table>
	<div style="text-align:right; margin-top:12px;padding:8px; border-top:1px solid #eee;">
	{buttons_html}
	</div>
	"""
	return html
