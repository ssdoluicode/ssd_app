import frappe

def drop_db_columns(doctype, fieldnames):
    table_name = f"tab{doctype}"

    # Check if table exists via SQL
    table_exists = frappe.db.sql(f"SHOW TABLES LIKE '{table_name}'")
    if not table_exists:
        frappe.log(f"Table `{table_name}` does not exist. Skipping.")
        return

    # Get all columns safely
    columns = [row[0] for row in frappe.db.sql(f"SHOW COLUMNS FROM `{table_name}`")]

    for fieldname in fieldnames:
        if fieldname in columns:
            frappe.db.sql(f'ALTER TABLE `{table_name}` DROP COLUMN `{fieldname}`')
            frappe.log(f"Dropped column `{fieldname}` from `{table_name}`")
        else:
            frappe.log(f"Column `{fieldname}` does not exist in `{table_name}`")

def execute():
    delete_map = {
        "CIF Sheet":["customer", "notify", "shipping_company", "payment_term", "term_days", "bank"],
        "Doc Nego Details": ["nego_date", "nego_amount", "bank", "payment_term", "cif_id"],
        "Doc Refund Details" : ["refund_date", "refund_amount", "interest_from", "bank", "interest_on", "cif_id"],
        "Doc Received Details" : ["received_date", "bank", "received_amount", "cif_id"],


    }

    for doctype, fieldnames in delete_map.items():
        drop_db_columns(doctype, fieldnames)

    frappe.db.commit()
    frappe.log("Database columns deleted successfully.")
