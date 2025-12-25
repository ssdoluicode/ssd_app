from frappe.model.document import Document
import frappe
from frappe import _
from frappe.utils import flt

class CCReceived(Document):
    def validate(self):
        self.validate_child_rows()
        self.validate_amount_sum()

    def validate_child_rows(self):
        ref_no_set = set()
        for idx, row in enumerate(self.cc_breakup, start=1):
            # Non-zero amount check
            if flt(row.amount) == 0:
                frappe.throw(_("Row {0}: Amount cannot be zero.").format(idx))
            
            # Unique Ref No check
            ref = (row.ref_no or "").strip()
            if not ref:
                frappe.throw(_("Row {0}: Ref No is required.").format(idx))
            if ref in ref_no_set:
                frappe.throw(_("Row {0}: Duplicate Ref No '{1}'.").format(idx, ref))
            ref_no_set.add(ref)

    def validate_amount_sum(self):
        total_breakup = sum(flt(row.amount) for row in self.cc_breakup)
        # Using a small epsilon for float comparison to avoid precision issues
        if abs(flt(self.amount_usd) - total_breakup) > 0.01:
            frappe.throw(
                _("Total Breakup Amount ({0}) must equal Amount USD ({1})")
                .format(total_breakup, self.amount_usd)
            )

@frappe.whitelist()
def cc_balance_breakup(customer, as_on):
    """
    Calculates balance per reference without using Pandas.
    """
    # 1. Get CC from CIF Sheets
    inv_data = frappe.get_all("CIF Sheet", 
        filters={"customer": customer, "inv_date": ["<=", as_on], "cc": ["!=", 0]},
        fields=["inv_no as ref_no", "cc as amount"]
    )

    # 2. Get already received CC from Breakup table
    received_entries = frappe.db.sql("""
        SELECT ccb.ref_no, SUM(ccb.amount) as amount
        FROM `tabCC Breakup` ccb
        JOIN `tabCC Received` ccr ON ccb.parent = ccr.name
        WHERE ccr.customer = %s AND ccr.date <= %s
        GROUP BY ccb.ref_no
    """, (customer, as_on), as_dict=True)

    # 3. Consolidate balances
    balances = {}
    for d in inv_data:
        balances[d.ref_no] = balances.get(d.ref_no, 0) + flt(d.amount)
    
    for d in received_entries:
        balances[d.ref_no] = balances.get(d.ref_no, 0) - flt(d.amount)

    # 4. Generate HTML
    rows_html = ""
    total = 0
    for ref_no, amt in balances.items():
        if round(amt, 2) != 0:
            total += amt
            rows_html += f"""
                <tr>
                    <td>{ref_no}</td>
                    <td style="text-align: right;">{amt:,.2f}</td>
                </tr>"""

    if not rows_html:
        return _("<div class='text-muted'>No outstanding CC balance found.</div>")

    return f"""
        <table class="table table-bordered" style="width: 100%;">
            <thead style="background-color: #f8f9fa;">
                <tr><th>Ref No</th><th style="text-align: right;">Balance</th></tr>
            </thead>
            <tbody>{rows_html}</tbody>
            <tfoot>
                <tr style="font-weight: bold;">
                    <td>Total</td><td style="text-align: right;">{total:,.2f}</td>
                </tr>
            </tfoot>
        </table>"""