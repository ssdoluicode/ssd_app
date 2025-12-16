import frappe

def update_doctype(doctype):
    docs = frappe.get_all(
        doctype,
        fields=["name", "invoice_no"]
    )

    for d in docs:
        # Get invoice number from CIF Sheet
        if not d.invoice_no:
            continue  # avoid titles like "NAME ()"

        custom_title = f"{d.name} ({d.invoice_no})"

        # Update fields
        frappe.db.set_value(
            doctype,
            d.name,
            "custom_title",
            custom_title,
            update_modified=False
        )
    print(f"Updated records in {doctype}")
    frappe.logger().info(f"Updated records in {doctype}")


def execute():
    update_doctype("Interest Paid")

    frappe.db.commit()

    frappe.logger().info("Completed patch: Updated titles, invoice_no, cif_id in all doctypes")
