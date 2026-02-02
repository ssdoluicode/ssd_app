# Copyright (c) 2026, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import now_datetime, time_diff_in_seconds


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
    
    def on_trash(self):
        self.protect_delete()

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
                sub_limit_amount= frappe.db.get_value("Banking Line Sub Limit", row.banking_line, "sub_limit_amount")
                print(sub_limit_amount , combind_limit)
                if not no_limit and sub_limit_amount > combind_limit:
                    frappe.throw(
                    f"❌ Row {row.idx}: Individual Limit '{row.banking_line}' "
                    f"{sub_limit_amount:,.2f} exceeds combined allowed limit "
                    f"{combind_limit:,.2f} for banking line "
                    f"{row.combind_banking_line_name} "
                )
           

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


    def protect_delete(self, hours=1):
        """
        Protect document deletion beyond a given time limit.

        :param doc: Frappe Document (self)
        :param hours: Allowed delete time in hours (default: 1 hour)
        """

        if not self.creation:
            return

        diff_seconds = time_diff_in_seconds(
            now_datetime(),
            self.creation
        )

        allowed_seconds = hours * 3600

        if diff_seconds > allowed_seconds:
            frappe.throw(
                f"❌ Deletion allowed only within {hours} hour(s) of creation."
            )

        



