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
        # self.validate_unique_bank_com()
        self.validate_individual_line()

    def before_save(self):
        self.set_calculated_field()
    # --------------------------------------------------
    # bank + com must be unique
    # --------------------------------------------------
    # def validate_unique_bank_com(self):

    #     if not self.bank or not self.company:
    #         return

    #     existing = frappe.db.exists(
    #         "Com Banking Line",
    #         {
    #             "bank": self.bank,
    #             "company": self.company,
    #             "name": ["!=", self.name]
    #         }
    #     )

    #     if existing:
    #         frappe.throw(
    #             _("Combination of Bank <b>{0}</b> and Company <b>{1}</b> already exists.")
    #             .format(self.bank, self.company),
    #             title=_("Duplicate Entry")
    #         )

    # def validate_individual_line(self):
    #     for row in self.banking_line_details:
    #         banking_line_name=frappe.get_value("Bank Banking Line",row.combind_banking_line, "banking_line_name" )
    #         row.combind_banking_line_name = banking_line_name

    #         combind_limit_result = frappe.db.sql("""
    #             SELECT b_bl.banking_line AS combind_limit, no_limit
    #             FROM `tabBank Banking Line` b_bl
    #             WHERE b_bl.banking_line_name = %s
    #             AND b_bl.date < %s
    #             ORDER BY b_bl.date DESC, b_bl.creation DESC
    #             LIMIT 1
    #         """, (banking_line_name, self.date), as_dict=True)

    #         # Safely extract values
    #         if combind_limit_result:
    #             combind_limit = combind_limit_result[0].get("combind_limit") or 0
    #             no_limit = combind_limit_result[0].get("no_limit") or 0
    #         else:
    #             combind_limit = 0
    #             no_limit = 0


    #         if row.individual_limit:
    #             if not no_limit and row.banking_line > combind_limit:
    #                 frappe.throw(f"Individual Limit {row.banking_line} exceeds combined allowed limit {combind_limit}")

    #         else:
    #             row.banking_line = 0

    def validate_individual_line(self):
        seen_payment_terms = set()  # To track unique payment terms

        for row in self.banking_line_details:
            # 1. Set the combined banking line name
            banking_line_name = frappe.get_value(
                "Bank Banking Line", row.combind_banking_line, "banking_line_name"
            )
            row.combind_banking_line_name = banking_line_name

            # 2. Fetch the latest combined limit
            combind_limit_result = frappe.db.sql("""
                SELECT b_bl.banking_line AS combind_limit, no_limit
                FROM `tabBank Banking Line` b_bl
                WHERE b_bl.banking_line_name = %s
                AND b_bl.date <= %s
                ORDER BY b_bl.date DESC, b_bl.creation DESC
                LIMIT 1
            """, (banking_line_name, self.date), as_dict=True)

            # Safely extract values
            if combind_limit_result:
                combind_limit = combind_limit_result[0].get("combind_limit") or 0
                no_limit = combind_limit_result[0].get("no_limit") or 0
            else:
                combind_limit = 0
                no_limit = 0

            # 3. Validate individual limit against combined limit
            if row.individual_limit:
                if not no_limit and row.banking_line > combind_limit:
                    frappe.throw(
                        f"Individual Limit {row.banking_line} exceeds combined allowed limit {combind_limit} "
                        f"for banking line {row.combind_banking_line_name} and payment term {row.payment_term}"
                    )
            else:
                row.banking_line = 0

            # 4. Validate payment_term uniqueness
            if row.payment_term in seen_payment_terms:
                frappe.throw(f"Duplicate Payment Term '{row.payment_term}' found in banking line details")
            seen_payment_terms.add(row.payment_term)



    def set_calculated_field(self):
        if not self.bank or not self.company:
            frappe.throw("Bank and Company are mandatory")

        self.bank_com_id = f"{self.bank}:{self.company}"

        for idx, row in enumerate(self.banking_line_details, start=1):

            if not row.combind_banking_line:
                frappe.throw(
                    f"Row {idx}: Combined Banking Line is mandatory"
                )

            banking_line_name = frappe.get_value(
                "Bank Banking Line",
                row.combind_banking_line,
                "banking_line_name"
            )

            if not banking_line_name:
                frappe.throw(
                    f"Row {idx}: Banking Line Name not found for "
                    f"Bank Banking Line '{row.combind_banking_line}'"
                )

            row.combind_banking_line_name = banking_line_name


    



