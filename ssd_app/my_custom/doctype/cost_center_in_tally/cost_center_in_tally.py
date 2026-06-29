# Copyright (c) 2026, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class CostCenterinTally(Document):
    def validate(self):
        if self.inv_no:
            company, invoice_no = frappe.db.get_value(
                "CIF Sheet",
                self.inv_no,
                ["accounting_company", "invoice_no"]
            )

            if not self.company:
                self.company = company

            if not self.invoice_no:
                self.invoice_no = invoice_no
                
            if not self.entry_date:
                self.entry_date = today()
