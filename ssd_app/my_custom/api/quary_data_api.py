
import frappe
import re

@frappe.whitelist(allow_guest=True)
def get_public_report(quary=None):
    """
    Public API to fetch data securely.
    - Only allows SELECT queries.
    - Users can fetch complex joins, but cannot UPDATE/DELETE/INSERT/DROP.
    """
    if not quary:
        return {"message": []}

    try:
        # Normalize query
        q_lower = quary.strip().lower()

        if not q_lower.startswith("select"):
            return
            # return {"message": []}

        # 2️⃣ Block dangerous keywords anywhere in the query
        dangerous_keywords = ["update", "delete", "insert", "drop", "truncate", "alter"]
        if any(k in q_lower for k in dangerous_keywords):
            return
            # return {"message": [], "error": "Query contains forbidden operations"}

        # 3️⃣ Execute the query safely
        data = frappe.db.sql(quary, as_dict=True)
        return data

    except Exception as e:
        return {"message": [], "error": str(e)}
