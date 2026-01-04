# Copyright (c) 2026, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


@frappe.whitelist()
def banking_line_filter(doctype, txt, searchfield, start, page_len, filters):
    bank = filters.get("bank")

    return frappe.db.sql("""
        SELECT
            name, custom_title
        FROM `tabBank Banking Line`
        WHERE bank = %s
          AND custom_title LIKE %s
        ORDER BY name
        LIMIT %s OFFSET %s
    """, (
        bank,
        f"%{txt}%",
        page_len,
        start
    ))



class ComBankingLine(Document):

    def validate(self):
        self.validate_unique_bank_com()
        self.validate_individual_line()

    # --------------------------------------------------
    # bank + com must be unique
    # --------------------------------------------------
    def validate_unique_bank_com(self):

        if not self.bank or not self.company:
            return

        existing = frappe.db.exists(
            "Com Banking Line",
            {
                "bank": self.bank,
                "company": self.company,
                "name": ["!=", self.name]
            }
        )

        if existing:
            frappe.throw(
                _("Combination of Bank <b>{0}</b> and Company <b>{1}</b> already exists.")
                .format(self.bank, self.company),
                title=_("Duplicate Entry")
            )

    def validate_individual_line(self):
        for row in self.banking_line_details:
            banking_line_name=frappe.get_value("Bank Banking Line",row.combind_banking_line, "banking_line_name" )

            combind_limit_result = frappe.db.sql("""
                SELECT SUM(b_bl.banking_line) as total_limit
                FROM `tabBank Banking Line` b_bl
                WHERE b_bl.banking_line_name = %s
                AND b_bl.date < %s
            """, (banking_line_name, self.date), as_dict=True)

            # Safely extract the limit
            combind_limit = combind_limit_result[0].get("total_limit") if combind_limit_result else 0

            if row.individual_limit:
                if row.banking_line > combind_limit:
                    frappe.throw(f"Individual Limit {row.banking_line} exceeds combined allowed limit {combind_limit}")

            else:
                row.banking_line = combind_limit





