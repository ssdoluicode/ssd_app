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
        shi_id = frappe.db.get_value(
            "CIF Sheet",
            d.inv_no,
            "inv_no" 
        )

        if not shi_id:
            continue

        frappe.db.set_value(
            doctype,
            d.name,
            {
                "inv_no": shi_id ,
                "shipping_id": shi_id
            },
            update_modified=False
        )

    frappe.logger().info(f"Updated {doctype} with Shipping Book links")

def execute():
    update_doctype("Doc Nego")
    update_doctype("Doc Refund")
    update_doctype("Doc Received")
    frappe.db.commit()
