# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
def set_custom_title(doc):

	# Strip and combine
	doc.custom_title = f"{doc.lc_no.strip()} :: {doc.inv_no.strip()}".strip()
	# doc.title = doc.custom_title



class LCPayment(Document):
	def before_save(self):
		if self.lc_no and self.inv_no:
			set_custom_title(self)
