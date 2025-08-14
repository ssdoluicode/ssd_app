# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
# from datetime import datetime, timedelta
from frappe.utils import getdate, add_days
import json
import pandas as pd
import numpy as np


from ssd_app.utils.banking import export_banking_data


def calculate_term_days(doc):
    if doc.bank_due_date and doc.nego_date:
        due_date = getdate(doc.bank_due_date)
        nego_date = getdate(doc.nego_date)

        if due_date > nego_date:
            doc.term_days = (due_date - nego_date).days
        else:
            frappe.throw(
                title="Invalid Date",
                msg="Bank Due Date must be after Negotiation Date."
            )

def calculate_due_date(doc):
    if doc.term_days and doc.nego_date and not doc.bank_due_date:
        if doc.term_days > 0:
            nego_date = getdate(doc.nego_date)
            doc.bank_due_date = add_days(nego_date, doc.term_days)
        else:
            frappe.throw(
                title="Invalid Term Days",
                msg="Term Days must be a positive integer."
            )


def final_validation(doc):
    if not doc.inv_no:
        return

    # Fetch CIF document value
    cif_data = frappe.db.get_value("CIF Sheet", doc.inv_no, ["document", "inv_date"], as_dict=True)
    cif_document = cif_data.document or 0
    inv_date = cif_data.inv_date or ""

    # Total received from other Doc Received entries (excluding current one)
    total_received = frappe.db.sql("""
        SELECT IFNULL(SUM(received), 0)
        FROM `tabDoc Received`
        WHERE inv_no = %s 
    """, (doc.inv_no))[0][0] or 0

    # Total nego from other Doc Nego entries (excluding current one)
    total_nego = frappe.db.sql("""
        SELECT IFNULL(SUM(nego_amount), 0)
        FROM `tabDoc Nego`
        WHERE inv_no = %s AND name != %s 
    """, (doc.inv_no, doc.name))[0][0] or 0

    # Can Nego calculation
    can_nego = round((cif_document - total_nego) + min(total_nego - total_received, 0), 2)
    nego = doc.nego_amount or 0

    if doc.is_new() and nego > can_nego:
        frappe.throw(_(f"""
            ❌ <b>Nego amount exceeds the Document Amount.</b><br>
            <b>CIF Document Amount:</b> {cif_document:,.2f}<br>
            <b>Total Already Received:</b> {total_received:,.2f}<br>
            <b>Total Already Nego:</b> {total_nego:,.2f}<br>
            <b>Can Nego:</b> {can_nego:,.2f}<br>
            <b>This Entry:</b> {doc.nego_amount:,.2f}
        """))
        

    if (total_nego + doc.nego_amount)>cif_document:
        frappe.throw(_(f"""
            ❌ <b> Total Nego amount exceeds the Document Amount.</b><br>
            <b>CIF Document Amount:</b> {cif_document:,.2f}<br>
            <b>Total Already Nego:</b> {total_nego:,.2f}<br>
            <b>This Entry:</b> {doc.nego_amount:,.2f}
        """))


    nego_date = getdate(doc.nego_date) if doc.nego_date else None
    inv_date = getdate(cif_data.inv_date) if cif_data.inv_date else None

    if not inv_date:
        frappe.throw(_("🛑 Please set the <b>Invoice Date</b> before saving."))

    if not nego_date:
        frappe.throw(_("🛑 Please set the <b>Nego Date</b> before saving."))

    if nego_date < inv_date:
        frappe.throw(
            _("🛑 <b>Nego Date</b> cannot be before the <b>Invoice Date</b>. Please correct the dates."),
            title=_("Date Validation Error")
        )

def update_cif_bank_if_missing(doc):
    # Only update bank if it's missing
    bank = frappe.db.get_value("CIF Sheet", doc.inv_no, "bank")

    if bank:
        doc.bank=bank
        frappe.get_meta(doc.doctype).get_field("bank").read_only = 1

    else:
        if(doc.bank):
            frappe.db.set_value("CIF Sheet", doc.inv_no, "bank", doc.bank)
            # frappe.db.commit()
        else:
            frappe.throw('Bank name not put in CIF Sheet, Please input Bank name')
            

def protect_delete(doc):

    if frappe.db.exists("Doc Received", {"inv_no": doc.inv_no}):
        frappe.throw("❌ Cannot delete: Doc Already Received part or full")
    if frappe.db.exists("Doc Refund", {"inv_no": doc.inv_no}):
        frappe.throw("❌ Cannot delete: Doc Already Refunded")



def put_value_from_cif(doc):
    if doc.is_new():
        fields = ["inv_date", "category", "notify", "customer", "bank", "payment_term", "due_date"]
        data = frappe.db.get_value("CIF Sheet", doc.inv_no, fields, as_dict=True)

        if data:
            for field in fields:
                if not getattr(doc, field):  # only set if value is missing
                    setattr(doc, field, data.get(field))


class DocNego(Document): 
    def validate(self):
        final_validation(self)
        update_cif_bank_if_missing(self)
        calculate_term_days(self)
        calculate_due_date

    
    def before_save(self):
        put_value_from_cif(self)
    
    def on_trash(self):
        protect_delete(self)

@frappe.whitelist()
def get_cif_data(inv_no):
    cif = frappe.db.get_value(
        "CIF Sheet", inv_no,
        ["inv_date", "category", "notify", "customer",
         "bank", "payment_term", "term_days", "due_date", "document"],
        as_dict=True
    ) or {}

    total_received = frappe.db.sql("""
        SELECT IFNULL(SUM(received), 0)
        FROM `tabDoc Received`
        WHERE inv_no = %s
    """, (inv_no,))[0][0] or 0

    total_nego = frappe.db.sql("""
        SELECT IFNULL(SUM(nego_amount), 0)
        FROM `tabDoc Nego`
        WHERE inv_no = %s
    """, (inv_no,))[0][0] or 0
    doc= cif.get("document")
    cif["can_nego"]=(doc- total_nego) + min(total_nego-total_received,0)

    return cif

@frappe.whitelist()
def get_available_inv_no(doctype, txt, searchfield, start, page_len, filters):
    query = """
    SELECT cif.name, cif.inv_no
    FROM `tabCIF Sheet` AS cif
    LEFT JOIN (
        SELECT inv_no, SUM(received) AS total_received
        FROM `tabDoc Received`
        GROUP BY inv_no
    ) AS dr ON dr.inv_no = cif.name
    LEFT JOIN (
        SELECT inv_no, SUM(nego_amount) AS total_nego
        FROM `tabDoc Nego`
        GROUP BY inv_no
    ) AS dn ON dn.inv_no = cif.name
    WHERE cif.document > 0
        AND cif.payment_term != 'TT'
        AND cif.inv_no LIKE %s
        AND ROUND(
            (cif.document - IFNULL(dn.total_nego, 0)) 
            + LEAST(IFNULL(dn.total_nego, 0) - IFNULL(dr.total_received, 0), 0),
            2
        ) > 0
    ORDER BY cif.inv_no ASC
    LIMIT %s, %s
    """
    return frappe.db.sql(query, (f"%{txt}%", start, page_len))





@frappe.whitelist()
def export_banking_line(as_on, columns_order=[]):

    data = export_banking_data(as_on)

    if not data:
        return "<p>No data found</p>"

    df = pd.DataFrame(data)
    if columns_order:
        if isinstance(columns_order, str):
            columns_order = json.loads(columns_order)
    else:
        columns_order = None  # No order specified
        columns_order = sorted(df["p_term"].dropna().unique().tolist())


    pivot = (
        df.pivot_table(
            index=["bank", "com"],
            columns="p_term",
            values="nego",
            aggfunc="sum",
            fill_value=0.0
        )
        .reindex(columns=columns_order, fill_value=0.0)
        .sort_index(level=[0, 1])
    )

    display_vals = pivot.replace(0.0, np.nan)

    css = """
        <style>
        table.bank-summary { 
            border-collapse: separate !important;
            border-spacing: 0;
            width: 100%; 
            color:black;
            font-family: Arial, sans-serif; 
            font-size: 13px; 
            border: 1px solid #ccc;
            border-radius: 8px;
            overflow: hidden;
        }

        .bank-summary th, .bank-summary td { 
            border: 1px solid #ddd;
            padding: 6px 10px; 
        }

        .bank-summary th { 
            text-align: center; 
            font-weight: bold;
            color: white; 
            white-space: nowrap;
            background: linear-gradient(#4a6fa5, #3d5e8b); /* modern blue */
            border-top: none;
        }

        .bank-summary th:first-child { border-top-left-radius: 8px; }
        .bank-summary th:last-child { border-top-right-radius: 8px; }

        /* Row hover effect */
        .bank-summary tbody tr:hover {
            background-color: #eef5ff;
        }

        .bank-summary td.num { text-align: right; white-space: nowrap; }
        .bank-summary td.txt { text-align: left; }
        .bank-summary td.blank { text-align: center; color: #555; }

        /* New softer colors */
        .bank-row-even { background-color: #f8fbff; }
        .bank-row-odd  { background-color: #fdfcfb; }
        .total { font-weight: bold; background-color: #d4f8d4; }
        
        </style>

        """

    html = [css, '<table class="bank-summary">']
    html.append("<thead><tr><th>Bank</th><th>Company</th>")
    for col in columns_order:
        html.append(f"<th>{col}</th>")
    html.append("</tr></thead><tbody>")

    # Grand totals
    grand_totals = display_vals.copy().fillna(0.0).sum(axis=0)

    # Bank colors
    bank_colors = ["bank-row-even", "bank-row-odd"]
    color_idx = 0

    # Loop through banks
    for bank, bank_frame in display_vals.groupby(level=0):
        bank_rows = bank_frame.reset_index(level=0, drop=True)
        rowspan = len(bank_rows)
        first_row = True
        row_class = bank_colors[color_idx % 2]
        color_idx += 1

        for company, row in bank_rows.iterrows():
            html.append(f'<tr class="{row_class}">')
            if first_row:
                html.append(f'<td class="txt" rowspan="{rowspan}">{bank}</td>')
                first_row = False
            html.append(f'<td class="txt">{company}</td>')
            for col in columns_order:
                val = row.get(col, np.nan)
                if pd.isna(val):
                    html.append('<td class="blank">-</td>')
                else:
                    html.append(f'<td class="num">{val:,.2f}</td>')
            html.append("</tr>")

    # Grand total row
    html.append('<tr class="total"><td class="txt" style = "text-align: center;" colspan="2">TOTAL</td>')
    for col in columns_order:
        tot = grand_totals.get(col, 0.0)
        if tot == 0.0 or pd.isna(tot):
            html.append('<td class="blank">-</td>')
        else:
            html.append(f'<td class="num">{tot:,.2f}</td>')
    html.append("</tr>")

    html.append("</tbody></table>")
    return "".join(html)


