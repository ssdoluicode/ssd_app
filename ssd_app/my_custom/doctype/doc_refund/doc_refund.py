# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

# ----------------------------
# 🔁 Utility: Aggregate sums by inv_no
# ----------------------------
def get_total(table, field, inv_no, exclude_name=None):
    condition = "AND name != %(exclude_name)s" if exclude_name else ""
    params = {"inv_no": inv_no}
    if exclude_name:
        params["exclude_name"] = exclude_name

    return frappe.db.sql(f"""
        SELECT IFNULL(SUM({field}), 0)
        FROM `tab{table}`
        WHERE inv_no = %(inv_no)s {condition}
    """, params)[0][0]

# ----------------------------
# 🔎 Validate refund entry
# ----------------------------
def final_validation(doc):
    total_received = get_total("Doc Received", "received", doc.inv_no)
    total_nego     = get_total("Doc Nego", "nego_amount", doc.inv_no)
    total_ref      = get_total("Doc Refund", "refund_amount", doc.inv_no, exclude_name=doc.name)

    pending_nego = max(total_nego - total_received - total_ref, 0)

    if doc.is_new() and pending_nego < doc.refund_amount:
        frappe.throw(f"""
            ❌ <b>Refund amount exceeds the Nego Amount.</b><br>
            <b>Total Nego Amount:</b> {total_nego:,.2f}<br>
            <b>Total Refund:</b> {total_ref:,.2f}<br>
            <b>Total Already Received:</b> {total_received:,.2f}<br>
            <b>Balance in Nego:</b> {pending_nego:,.2f}<br>
            <b>This Entry:</b> {doc.refund_amount:,.2f}
        """)

    if (total_ref + doc.refund_amount) > total_nego:
        frappe.throw(f"""
            ❌ <b>Total Refund amount exceeds the Nego Amount.</b><br>
            <b>Total Nego Amount:</b> {total_nego:,.2f}<br>
            <b>Total Refund (including this):</b> {(total_ref + doc.refund_amount):,.2f}
        """)


def protect_delete(doc):
    if frappe.db.exists("Doc Received", {"inv_no": doc.inv_no}):
        frappe.throw("❌ Cannot delete: Doc Already Received part or full")


def put_value_from_shi(doc):
    if doc.is_new():
        fields = ["customer", "bank", "notify", "payment_term"]
        data = frappe.db.get_value("Shipping Book", doc.inv_no, fields, as_dict=True)

        if data:
            for field in fields:
                if not getattr(doc, field):  # only set if value is missing
                    setattr(doc, field, data.get(field))



def set_calculated_fields(doc):
    invoice = frappe.db.get_value("Shipping Book", doc.inv_no, "inv_no")
    doc.custom_title = f"{doc.name} ({invoice})".strip()
    doc.invoice_no = invoice
    doc.shipping_id = doc.inv_no

# ----------------------------
# 📄 DocType Class
# ----------------------------
class DocRefund(Document):
    def validate(self):
        final_validation(self)

    def before_save(self):
        put_value_from_shi(self)
        set_calculated_fields(self)

    def on_trash(self):
        protect_delete(self)

# ----------------------------
# 🔍 For Link Field Filtering
# ----------------------------
@frappe.whitelist()
def get_available_inv_no(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT shi.name, shi.inv_no
        FROM (
            SELECT inv_no, SUM(nego_amount) AS total_nego
            FROM `tabDoc Nego` GROUP BY inv_no
        ) AS nego
        LEFT JOIN `tabShipping Book` AS shi ON shi.name = nego.inv_no
        LEFT JOIN (
            SELECT inv_no, SUM(received) AS total_rec
            FROM `tabDoc Received` GROUP BY inv_no
        ) AS rec ON rec.inv_no = nego.inv_no
        LEFT JOIN (
            SELECT inv_no, SUM(refund_amount) AS total_ref
            FROM `tabDoc Refund` GROUP BY inv_no
        ) AS ref ON ref.inv_no = nego.inv_no
        WHERE (COALESCE(nego.total_nego, 0) - COALESCE(ref.total_ref, 0)) > COALESCE(rec.total_rec, 0)
          AND (shi.name LIKE %(txt)s OR shi.inv_no LIKE %(txt)s)
        LIMIT %(start)s, %(page_len)s
    """, {
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })

# ----------------------------
# 🧠 Get shi data with computed nego amount
# ----------------------------
@frappe.whitelist()
def get_shi_data(inv_no):
    shi = frappe.db.get_value(
        "Shipping Book", inv_no,
        ["bl_date", "notify", "customer", "bank", "payment_term", "term_days", "document"],
        as_dict=True
    ) or {}

    total_received = get_total("Doc Received", "received", inv_no)
    total_nego     = get_total("Doc Nego", "nego_amount", inv_no)
    total_ref      = get_total("Doc Refund", "refund_amount", inv_no)

    shi["notify_name"]= frappe.db.get_value("Notify", shi.notify, "code")
    shi["customer_name"]= frappe.db.get_value("Customer", shi.customer, "customer")
    shi["bank_name"]= frappe.db.get_value("Bank", shi.bank, "bank")
    shi["nego_amount"] = total_nego - total_received - total_ref
    shi["payment_term_name"]= frappe.db.get_value("Payment Term", shi.payment_term, "term_name")
    return shi
