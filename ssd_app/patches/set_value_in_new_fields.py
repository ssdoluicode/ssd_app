import frappe

def update_doctype(doctype):
    docs = frappe.get_all(
        doctype,
        fields=["name", "inv_no"]
    )

    for d in docs:
        # Get invoice number from CIF Sheet
        invoice = frappe.db.get_value("CIF Sheet", d.inv_no, "inv_no") or ""

        # Update fields
        frappe.db.set_value(
            doctype,
            d.name,
            {
                "custom_title": f"{d.name} ({invoice})".strip(),
                "invoice_no": invoice,
                "cif_id": d.inv_no
            }
        )
    print(f"Updated records in {doctype}")
    frappe.logger().info(f"Updated records in {doctype}")


def execute():
    update_doctype("Doc Nego")
    update_doctype("Doc Refund")
    update_doctype("Doc Received")

    frappe.db.commit()

    frappe.logger().info("Completed patch: Updated titles, invoice_no, cif_id in all doctypes")
