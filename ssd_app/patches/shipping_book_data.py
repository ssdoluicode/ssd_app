import frappe

def update_doctype(doctype):

    docs = frappe.get_all(
        doctype,
        fields=[
            "name",
            "inv_no",
            "inv_date",
            "shipping_company",
            "customer",
            "notify",
            "document",
            "payment_term",
            "term_days",
            "sales",
            "bank"
        ]
    )

    for d in docs:

        # --------------------------------
        # Prevent duplicate Shipping Book
        # --------------------------------
        if frappe.db.exists("Shipping Book", {"source_doc": d.name}):
            continue

        sb = frappe.new_doc("Shipping Book")
        p_term= frappe.db.get_value("Payment Term", {"term_name":d.payment_term}, "name")

        # Source reference (VERY IMPORTANT)
        sb.source_doc = d.name

        sb.bl_date = d.inv_date
        sb.inv_no = d.inv_no
        sb.company = d.shipping_company
        sb.customer = d.customer
        sb.notify = d.notify

        # Accounting-safe assignment
        sb.invoice_amount = (
            d.document if d.document is not None else d.sales
        )

        sb.document = d.document
        sb.bank = d.bank
        sb.payment_term = p_term
        sb.term_days = d.term_days

        sb.insert(ignore_permissions=True)

    frappe.logger().info(f"Updated Shipping Book from {doctype}")


def execute():
    update_doctype("CIF Sheet")
    frappe.db.commit()
    frappe.logger().info(
        "Completed patch: Shipping Book created from CIF Sheet"
    )
