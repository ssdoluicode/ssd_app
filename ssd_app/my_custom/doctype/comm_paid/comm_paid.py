# # Copyright (c) 2025, SSDolui and contributors
# # For license information, please see license.txt

# import frappe
# from frappe.model.document import Document
# from frappe.utils import flt
# from frappe import _

# class CommPaid(Document):
#     def validate(self):
#         validate_comm_breakup(self)
#         validate_unique_inv_no(self)

# def validate_comm_breakup(doc):
#     """
#     Validate the comm Breakup child table:
#     - sum of amounts == amount_usd
#     - no blank/zero/negative amounts
#     """
#     total_amount = doc.amount_usd or 0
#     breakup_sum = sum(flt(d.amount) for d in doc.comm_breakup)

#     if total_amount <= 0:
#         frappe.throw(_("Amount USD should not be zero"))

#     if breakup_sum != total_amount:
#         frappe.throw(
#             _("Total of Comm Breakup amounts ({0}) must equal Amount USD ({1})")
#             .format(breakup_sum, total_amount)
#         )

#     for row in doc.comm_breakup:
#         if row.amount is None or row.amount <= 0:
#             frappe.throw(_("Each Comm Breakup row must have a positive amount and cannot be zero"))


# def validate_unique_inv_no(doc):
#     inv_no_set = set()
#     for idx, row in enumerate(doc.comm_breakup, start=1):
#         row.inv_no = (row.inv_no or "").strip()
#         if not row.inv_no:
#             frappe.throw(f"⚠️ Row {idx}: Inv No cannot be empty.")
#         if row.inv_no in inv_no_set:
#             frappe.throw(f"⚠️ Row {idx}: Inv No '{row.inv_no}' is duplicated in Comm Breakup.")
#         inv_no_set.add(row.inv_no)


# @frappe.whitelist()
# def inv_no_filter(doc):
# 	pass

# @frappe.whitelist()
# def get_filter_inv_no(doctype, txt, searchfield, start, page_len, filters=None):
#     filters = filters or {}
#     agent = filters.get("agent")

#     return frappe.db.sql(
#         """
#         SELECT
#             cost.name,
#             cost.custom_title,
#             cost.commission,
#             (cost.commission - IFNULL(cb.total_paid, 0)) AS balance,
#             IFNULL(cb.total_paid, 0) AS total_paid
#         FROM `tabCost Sheet` AS cost
#         LEFT JOIN (
#             SELECT inv_no, SUM(amount) AS total_paid
#             FROM `tabComm Breakup`
#             GROUP BY inv_no
#         ) cb ON cost.name = cb.inv_no
#         WHERE (%(agent)s IS NULL OR cost.agent = %(agent)s)
#           AND (cost.commission - IFNULL(cb.total_paid, 0)) != 0
#           AND cost.name LIKE %(txt)s
#         ORDER BY cost.name ASC
#         LIMIT %(page_len)s OFFSET %(start)s
#         """,
#         {
#             "agent": agent,
#             "txt": f"%{txt}%",
#             "page_len": page_len,
#             "start": start,
#         },
#         as_list=True,
#     )


#     # return frappe.db.sql(query, params)

# @frappe.whitelist()
# def get_inv_no_balance(inv_no):
#     balance = frappe.db.sql("""
#         SELECT 
#             (cost.commission - IFNULL(cb.total_paid, 0)) AS balance
#         FROM `tabCost Sheet` AS cost
#         LEFT JOIN (
#             SELECT inv_no, SUM(amount) AS total_paid
#             FROM `tabComm Breakup`
#             GROUP BY inv_no
#         ) cb ON cost.name = cb.inv_no
#         WHERE cost.name = %s
#     """, (inv_no,), as_dict=1)

#     if balance:
#         return balance[0].balance
#     return 0


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
                frappe.throw(_("Row {0}: Amount must be positive.").format(row.idx))
            
            # 2. Duplicate Check
            if row.inv_no in inv_nos:
                frappe.throw(_("Row {0}: Invoice {1} is duplicated.").format(row.idx, row.inv_no))
            inv_nos.append(row.inv_no)

            # 3. Balance Check (Server-side safety)
            balance = get_inv_no_balance(row.inv_no)
            if flt(row.amount) > flt(balance):
                frappe.throw(_("Row {0}: Amount ({1}) exceeds remaining balance ({2}) for Invoice {3}")
                             .format(row.idx, row.amount, balance, row.inv_no))
            
            total_allocated += flt(row.amount)

        # 4. Total Match Check
        if abs(flt(self.amount_usd) - total_allocated) > 0.001:
            frappe.throw(_("Total allocated ({0}) must equal Amount USD ({1})")
                         .format(total_allocated, self.amount_usd))

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
def get_inv_no_balance(inv_no):
    if not inv_no: return 0
    # Simplified query using COALESCE
    res = frappe.db.sql("""
        SELECT (c.commission - IFNULL(SUM(b.amount), 0))
        FROM `tabCost Sheet` c
        LEFT JOIN `tabComm Breakup` b ON c.name = b.inv_no
        WHERE c.name = %s
    """, (inv_no,))
    return flt(res[0][0]) if res else 0