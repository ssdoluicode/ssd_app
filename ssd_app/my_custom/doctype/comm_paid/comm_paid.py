# # Copyright (c) 2025, SSDolui and contributors
# # For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt
from frappe import _

class CommPaid(Document):
    def validate(self):
        self.validate_amount()
        self.validate_comm_breakup()

    def validate_amount(self):
        if flt(self.amount_usd) <= 0:
            frappe.throw(_("Amount USD must be greater than zero."))

    def validate_comm_breakup(self):
        if not self.comm_breakup:
            frappe.throw(_("Please add at least one row in the Commission Breakup table."))

        total_allocated = 0
        inv_nos = []

        for row in self.comm_breakup:
            # 1. Basic row validation
            if flt(row.amount) <= 0:
                frappe.throw(f"Row {row.idx}: Amount must be positive.")
            
            # 2. Duplicate Check
            if row.inv_no in inv_nos:
                frappe.throw(f"Row {row.idx}: Invoice { row.inv_no} is duplicated.")
            inv_nos.append(row.inv_no)

            # 3. Balance Check (Server-side safety)
            balance = get_inv_no_balance(row.inv_no, row.name)
            if flt(row.amount) > flt(balance):
                frappe.throw(f"Row {row.idx}: Amount {row.amount} exceeds remaining balance {balance} for Invoice {row.inv_no}")
            
            total_allocated += flt(row.amount)

        # 4. Total Match Check
        if abs(flt(self.amount_usd) - total_allocated) > 0.001:
            frappe.throw(f"Total allocated {total_allocated} must equal Amount USD ({self.amount_usd})")

@frappe.whitelist()
def get_filter_inv_no(doctype, txt, searchfield, start, page_len, filters=None):
    agent = filters.get("agent") if filters else None
    
    # Using a CTE (Common Table Expression) for better readability
    return frappe.db.sql("""
        WITH PaidInfo AS (
            SELECT inv_no, SUM(amount) AS total_paid
            FROM `tabComm Breakup`
            GROUP BY inv_no
        )
        SELECT 
            c.name, c.custom_title, c.commission, 
            (c.commission - IFNULL(p.total_paid, 0)) AS balance
        FROM `tabCost Sheet` c
        LEFT JOIN PaidInfo p ON c.name = p.inv_no
        WHERE (%(agent)s IS NULL OR c.agent = %(agent)s)
          AND (c.commission - IFNULL(p.total_paid, 0)) > 0
          AND (c.name LIKE %(txt)s OR c.custom_title LIKE %(txt)s)
        ORDER BY c.name ASC
        LIMIT %(page_len)s OFFSET %(start)s
    """, {
        "agent": agent,
        "txt": f"%{txt}%",
        "page_len": page_len,
        "start": start
    })

@frappe.whitelist()
def get_inv_no_balance(inv_no, name=None):
    if not inv_no:
        return 0

    conditions = ""
    values = [inv_no]

    if name:
        conditions = "AND name != %s"
        values.append(name)

    total = frappe.db.sql(f"""
        SELECT IFNULL(SUM(amount), 0)
        FROM `tabComm Breakup`
        WHERE inv_no = %s
        {conditions}
    """, values)[0][0]

    commission = frappe.db.get_value("Cost Sheet", inv_no, "commission") or 0

    return flt(commission) - flt(total)
