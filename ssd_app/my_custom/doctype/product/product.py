# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

# import frappe
# from frappe.model.document import Document

# # Create Custom Title 
# def set_custom_title(doc):
#     if not doc.product_group:
#         return

#     p_group, p_category_id = frappe.db.get_value("Product Group", doc.product_group, ["product_group", "product_category"],
#         as_dict=False
#     ) or ("", "")

#     product = doc.product or ""
#     doc.custom_title = f"{(p_group or '').strip()} :: {product.strip()}".strip()
#     doc.category = p_category_id
    
# class Product(Document):
# 	def before_save(self):
# 		set_custom_title(self)
# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

def validate_unique_custom_title(doc):
    """Check if intended custom_title is unique before setting."""
    if not doc.product_group:
        return

    # Compute what the custom_title would be
    p_group = frappe.db.get_value(
        "Product Group",
        doc.product_group,
        "product_group",
        as_dict=False
    ) or ""

    product = doc.product or ""
    intended_custom_title = f"{(p_group or '').strip()} :: {product.strip()}".strip()

    # Check if this custom_title already exists in another Product
    exists = frappe.db.exists(
        "Product",
        {
            "custom_title": intended_custom_title,
            "name": ["!=", doc.name]  # exclude self during update
        }
    )

    if exists:
        frappe.throw(f"Product '{product}' must be unique within Product Group '{p_group}'.")

    # If no duplicate, safe to set
    doc.custom_title = intended_custom_title

def set_category(doc):
    """Set category based on Product Group."""
    if not doc.product_group:
        return

    p_category_id = frappe.db.get_value(
        "Product Group",
        doc.product_group,"product_category",
        as_dict=False
    ) or ("", "")

    doc.category = p_category_id

class Product(Document):
    def validate(self):
        validate_unique_custom_title(self)  # Check before setting
        set_category(self)  # Set category separately
