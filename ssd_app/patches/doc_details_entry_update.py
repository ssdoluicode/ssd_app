import frappe

def update_doctype(doctype, p_dc):

    docs = frappe.get_all(
        doctype,
        fields=["name", "inv_no"]
    )

    for d in docs:
        if not d.inv_no:
            continue

        # Find Shipping Book linked by invoice number
        shi_id = frappe.db.get_value(
            p_dc,
            d.inv_no,
            "inv_no" 
        )

        if not shi_id:
            continue

        frappe.db.set_value(
            doctype,
            d.name,
            {
                "cif_id" : shi_id,
                "shipping_id": shi_id
            },
            update_modified=False
        )

    frappe.logger().info(f"Updated {doctype} with Shipping Book links")

def execute():
    update_doctype("Doc Nego Details", "Doc Nego")
    update_doctype("Doc Refund Details", "Doc Refund")
    update_doctype("Doc Received Details", "Doc Received")
    update_doctype("Interest Paid", "Doc Nego")
    frappe.db.commit()
