
import frappe
from frappe.utils import today
import pandas as pd
from ssd_app.utils.banking import export_banking_data, import_banking_data

def execute(filters=None):
    as_on = today()

    imp_data = import_banking_data(as_on) or []
    exp_data = export_banking_data(as_on) or []

    if not imp_data and not exp_data:
        return columns, []

    data = []

    # Import data
    for row in imp_data:
        # if row.get("p_term") not in ("LC at Sight", "LC"):
        data.append(row)

    # Export data (rename keys here)
    for row in exp_data:
        if row.get("p_term") in ("LC at Sight", "LC"):
            continue

        row["ref_no"] = row.pop("inv_no", None)
        row["amount_usd"] = row.pop("nego", None)
        data.append(row)

    columns = [
        {"label": "Inv/LC No", "fieldname": "ref_no", "fieldtype": "Data", "width": 150},
        # {"label": "Date", "fieldname": "date", "fieldtype": "Data", "width": 110},
        {"label": "Com", "fieldname": "com", "fieldtype": "Data", "width": 130},
        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 60},
        {"label": "P Term", "fieldname": "p_term", "fieldtype": "Data", "width": 90},
        {"label": "Amount", "fieldname": "amount_usd", "fieldtype": "Float", "width": 100},
    ]
    return columns, data
