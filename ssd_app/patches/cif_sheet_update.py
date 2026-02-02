import frappe

def update_doctype(doctype):

    docs = frappe.get_all(
        doctype,
        fields=["name", "inv_no"]
    )

    for d in docs:

        if not d.inv_no:
            continue

        # Find Shipping Book linked by invoice number
        shipping_book = frappe.db.get_value(
            "Shipping Book",
            {"inv_no": d.inv_no},
            "name"
        )

        if not shipping_book:
            continue

        frappe.db.set_value(
            doctype,
            d.name,
            {
                "invoice_no": d.inv_no,        # store invoice no
                "inv_no": shipping_book # Link field
            },
            update_modified=False
        )

    frappe.logger().info(f"Updated {doctype} with Shipping Book links")


def execute():
    update_doctype("CIF Sheet")
    frappe.db.commit()
