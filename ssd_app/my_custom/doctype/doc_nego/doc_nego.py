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
from frappe.utils import today



from ssd_app.utils.banking_line import check_banking_line, banking_line_data

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

def set_calculated_fields(doc):
    invoice = frappe.db.get_value("Shipping Book", doc.inv_no, "inv_no")
    doc.custom_title = f"{doc.name} ({invoice})".strip()
    doc.invoice_no = invoice
    doc.shipping_id= doc.inv_no
   

def final_validation(doc):
    if not doc.inv_no:
        return

    # Fetch document value
    shipping_data = frappe.db.get_value("Shipping Book", doc.inv_no, ["document", "bl_date", "bank"], as_dict=True)
    document = shipping_data.document or 0
    nego_date = getdate(doc.nego_date) if doc.nego_date else None
    bl_date = getdate(shipping_data.bl_date) if shipping_data.bl_date else None



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
    can_nego = round((document - total_nego) + min(total_nego - total_received, 0), 2)
    nego = doc.nego_amount or 0

    if doc.is_new() and nego > can_nego:
        frappe.throw(_(f"""
            ❌ <b>Nego amount exceeds the Document Amount.</b><br>
            <b>Document Amount:</b> {document:,.2f}<br>
            <b>Total Already Received:</b> {total_received:,.2f}<br>
            <b>Total Already Nego:</b> {total_nego:,.2f}<br>
            <b>Can Nego:</b> {can_nego:,.2f}<br>
            <b>This Entry:</b> {doc.nego_amount:,.2f}
        """))
        

    if (total_nego + doc.nego_amount)>document:
        frappe.throw(_(f"""
            ❌ <b> Total Nego amount exceeds the Document Amount.</b><br>
            <b>Document Amount:</b> {document:,.2f}<br>
            <b>Total Already Nego:</b> {total_nego:,.2f}<br>
            <b>This Entry:</b> {doc.nego_amount:,.2f}
        """))



    if not bl_date:
        frappe.throw(_("🛑 Please set the <b>Invoice Date</b> before saving."))

    if not nego_date:
        frappe.throw(_("🛑 Please set the <b>Nego Date</b> before saving."))

    if nego_date < bl_date:
        frappe.throw(
            _("🛑 <b>Nego Date</b> cannot be before the <b>Invoice Date</b>. Please correct the dates."),
            title=_("Date Validation Error")
        )
            

def protect_delete(doc):

    if frappe.db.exists("Doc Received", {"inv_no": doc.inv_no}):
        frappe.throw("❌ Cannot delete: Doc Already Received part or full")
    if frappe.db.exists("Doc Refund", {"inv_no": doc.inv_no}):
        frappe.throw("❌ Cannot delete: Doc Already Refunded")


def bank_line_validtation(doc):
    result = frappe.db.get_value("Shipping Book", doc.inv_no, ["company", "bank", "payment_term"] , as_dict=True)
   
    shipping_company = result["company"]
    bank = result["bank"]
    payment_term = result["payment_term"]
    
    if(not bank and not doc.bank_link):
        frappe.throw(_(f"""
                ❌ <b>Bank is Blank.</b><br>
                <b>Please put Bank Name in Shipping Book or Put here<br>
            """))
    if(not bank and doc.bank_link):
        bank= doc.bank_link

    bl_data=check_banking_line(bank, shipping_company, payment_term)
    bl = bl_data["balance_line"]

    if bl >= 0:
        if bl==0:
            frappe.throw("❌ No banking Line")
        if not doc.is_new():# need to add logic here
            actual_nego = frappe.db.get_value("Doc Nego", doc.name, "nego_amount")
            if doc.nego_amount > bl+actual_nego:
                frappe.throw(_(f"""
                ❌ <b>Nego amount exceeds Bank Line Limit.</b><br>
                <b>Banking Line Balance:</b> {bl+actual_nego:,.2f}<br>
                <b>Try to Entry:</b> {doc.nego_amount:,.2f}<br>
            """))
        elif doc.nego_amount > bl:
            frappe.throw(_(f"""
            ❌ <b>Nego amount exceeds Bank Line Limit.</b><br>
            <b>Banking Line Balance:</b> {bl:,.2f}<br>
            <b>Try to Entry:</b> {doc.nego_amount:,.2f}<br>
        """))
            
def set_shipping_book_bank(doc): #set bank if missing in shipping book
    shipping_bank = frappe.db.get_value("Shipping Book",doc.inv_no,"bank")

    if not shipping_bank and doc.bank_link:
        frappe.db.set_value("Shipping Book",doc.inv_no,"bank",doc.bank_link)
   



from datetime import date
class DocNego(Document): 

    def validate(self):
        final_validation(self)
        bank_line_validtation(self)
        
    def before_save(self):
        calculate_term_days(self)
        calculate_due_date(self)
        set_calculated_fields(self)
        set_shipping_book_bank(self)
    
    def on_trash(self):
        protect_delete(self)


@frappe.whitelist()
def get_shi_data(inv_no):
    # Fetch Shipping Book safely by inv_no field
    shi = frappe.db.get_value(
        "Shipping Book",inv_no,
        [
            "bl_date",
            "term_days",
            "payment_term",
            "bank",
            "document"
        ],
        as_dict=True
    ) or {}

    # Defaults (important!)
    term_days = shi.get("term_days") or 0
    payment_term = shi.get("payment_term") or ""
    bank = shi.get("bank")
    document_amt = shi.get("document") or 0

    # Total Received
    total_received = frappe.db.sql("""
        SELECT IFNULL(SUM(received), 0)
        FROM `tabDoc Received`
        WHERE inv_no = %s
    """, (inv_no,), as_dict=False)[0][0] or 0

    # Total Negotiated
    total_nego = frappe.db.sql("""
        SELECT IFNULL(SUM(nego_amount), 0)
        FROM `tabDoc Nego`
        WHERE inv_no = %s
    """, (inv_no,), as_dict=False)[0][0] or 0

    # Bank Code (safe)
    shi["bank_name"] = None
    if bank:
        shi["bank_name"] = frappe.db.get_value("Bank", bank, "bank")
    
    shi["p_term_name"] = None
    if payment_term:
        shi["p_term_name"] = frappe.db.get_value("Payment Term", payment_term, "term_name")

    # Can Nego calculation (safe math)
    shi["can_nego"] = (
        (document_amt - total_nego)
        + min(total_nego - total_received, 0)
    )

    return shi


@frappe.whitelist()
def get_available_inv_no(doctype, txt, searchfield, start, page_len, filters):
    query = """
    SELECT shi.name, shi.inv_no
    FROM `tabShipping Book` AS shi
    LEFT JOIN (
        SELECT inv_no, SUM(received) AS total_received
        FROM `tabDoc Received`
        GROUP BY inv_no
    ) AS dr ON dr.inv_no = shi.name
    LEFT JOIN (
        SELECT inv_no, SUM(nego_amount) AS total_nego
        FROM `tabDoc Nego`
        GROUP BY inv_no
    ) AS dn ON dn.inv_no = shi.name
    WHERE shi.document > 0
        AND shi.payment_term != 'TT'
        AND shi.inv_no LIKE %s
        AND ROUND(
            (shi.document - IFNULL(dn.total_nego, 0)) 
            + LEAST(IFNULL(dn.total_nego, 0) - IFNULL(dr.total_received, 0), 0),
            2
        ) > 0
    ORDER BY shi.inv_no ASC
    LIMIT %s, %s
    """
    return frappe.db.sql(query, (f"%{txt}%", start, page_len))


@frappe.whitelist()
def used_banking_line(as_on, columns_order=[]):
    columns_order = frappe.get_all(
        "Payment Term",
        filters={
            "active": 1,
            "use_banking_line": 1
        },
        pluck="term_name",
        order_by="term_name"
    )
    # Use dict comprehension for fast mapping
    company_map = {d.name: d.company_code for d in frappe.get_all("Company", fields=["name", "company_code"])}
    bank_map = {d.name: d.bank for d in frappe.get_all("Bank", fields=["name", "bank"])}
    payment_term_map = {d.name: d.term_name for d in frappe.get_all("Payment Term", fields=["name", "term_name"])}
    banking_data= banking_line_data()
    for row in banking_data:
        company_name = row.get("company")
        bank_name = row.get("bank")
        payment_term_name = row.get("payment_term")
        row["company"] = company_map.get(company_name, company_name)
        row["bank"] = bank_map.get(bank_name, bank_name)
        row["payment_term"] = payment_term_map.get(payment_term_name, payment_term_name)

    df= pd.DataFrame(banking_data)
    pivot = (
        df.pivot_table(
            index=["bank", "company"],
            columns="payment_term",
            values="used_line",
            aggfunc="sum",
            fill_value=0.0
        )
        .sort_index(level=[0, 1])
    )

    # Convert 0 → NaN only for display logic
    display_vals = pivot.replace(0.0, np.nan)

    # Drop rows where ALL values are NaN
    display_vals = display_vals.loc[display_vals.notna().any(axis=1)]


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

        

        .bank-summary td.num { text-align: right; white-space: nowrap; }
        .bank-summary td.txt { text-align: left; }
        .bank-summary td.blank { text-align: center; color: #555; }

        /* New softer colors */
        .bank-row-even { background-color: #f8fbff;}
        .bank-row-odd  { background-color: #fdfcfb;}
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
    html.append('<tr class="total"><td class="txt" colspan="2" style = "text-align: center; ">TOTAL</td>')
    for col in columns_order:
        tot = grand_totals.get(col, 0.0)
        if tot == 0.0 or pd.isna(tot):
            html.append('<td class="blank">-</td>')
        else:
            html.append(f'<td class="num">{tot:,.2f}</td>')
    html.append("</tr>")

    html.append("</tbody></table>")
    return "".join(html)


@frappe.whitelist()
def update_export_due_date(docname, new_due_date, due_date_confirm, note= None):
    """Update due date and confirmation flag"""
    frappe.db.set_value("Doc Nego", docname, {
        "bank_due_date": new_due_date,
        "due_date_confirm": int(due_date_confirm),
        "note": note or ""
    })
    return "success"


@frappe.whitelist()
def update_import_due_date(doctype_name,docname, new_due_date, due_date_confirm, note=None):
    """Update due date and confirmation flag"""
    frappe.db.set_value(doctype_name, docname, {
        "due_date": new_due_date,
        "due_date_confirm": int(due_date_confirm),
        "note": note or ""
    })
    return "success"


@frappe.whitelist()
def get_doc_int_summary(id_name, id, as_on= None):
    """
    Returns CIF financial summary as dict.
    Args:
        cif_id (str): CIF ID like 'cif-0000145'
        as_on (str): Date 'YYYY-MM-DD'
    """
    rec_date="0000-00-00"
    ref_date="0000-00-00"
    rec_amount=0
    ref_amount=0
    bank= None
    if id_name == "nego":
        data = frappe.db.get_value("Doc Nego", id, ["shipping_id", "inv_no"],as_dict=True)
        shipping_id = data.shipping_id
        bank = frappe.db.get_value("Shipping Book", data.inv_no, "bank")
        bank_name = frappe.db.get_value("Bank", bank, "bank")

    elif id_name == "rec":
        data = frappe.db.get_value("Doc Received",id,["shipping_id", "received_date", "received", "inv_no"],as_dict=True)
        shipping_id = data.shipping_id
        rec_date = data.received_date
        rec_amount = data.received
        as_on= data.received_date
        bank = frappe.db.get_value("Shipping Book", data.inv_no, "bank")
        bank_name = frappe.db.get_value("Bank", bank, "bank")

    elif id_name == "ref":
        data = frappe.db.get_value("Doc Refund",id,["shipping_id", "refund_date", "refund_amount", "inv_no"],as_dict=True)
        shipping_id = data.shipping_id
        ref_date = data.refund_date
        ref_amount = data.refund_amount
        as_on= data.refund_date
        bank = frappe.db.get_value("Shipping Book", data.inv_no, "bank")
        bank_name = frappe.db.get_value("Bank", bank, "bank")

    query = f"""
        SELECT
            n.shipping_id,
            n.nego_date,
            n.nego_amount,
            NULLIF(rec_d.rec_amount,0) AS total_rec_amount,
            NULLIF(ref.ref_amount,0) AS total_ref_amount,

            -- Final MAX interest_upto_date
            NULLIF(
                GREATEST(
                    COALESCE(n.nego_int_upto, '0000-00-00'),
                    COALESCE(i.int_int_upto, '0000-00-00'),
                    COALESCE(rec_d.rec_int_upto, '0000-00-00'),
                    COALESCE(ref.ref_int_upto, '0000-00-00')
                ), '0000-00-00'
            ) AS int_upto,

            -- Final MAX interest_pct
            NULLIF(
                GREATEST(
                    COALESCE(n.nego_int_pct, 0),
                    COALESCE(i.int_int_pct, 0),
                    COALESCE(rec_d.rec_int_pct, 0),
                    COALESCE(ref.ref_int_pct, 0)
                ), 0
            ) AS int_pct,

            -- Balance liability
            NULLIF(GREATEST((n.nego_amount - COALESCE(rec_d.bank_liab,0) - COALESCE(ref.ref_amount,0)), 0),0) AS b_liab

        FROM (
            SELECT
                nd.shipping_id,
                SUM(n.nego_amount) AS nego_amount,
                MAX(n.nego_date) AS nego_date,
                MAX(nd.interest_upto_date) AS nego_int_upto,
                MAX(nd.interest_pct) AS nego_int_pct
            FROM `tabDoc Nego Details` nd
            LEFT JOIN `tabDoc Nego` n ON n.name= nd.inv_no
            WHERE nd.shipping_id = %s
              AND n.nego_date < %s
            GROUP BY nd.shipping_id
        ) AS n

        LEFT JOIN (
            SELECT
                ip.shipping_id,
                MAX(ip.interest_rate) AS int_int_pct,
                MAX(ip.interest_upto_date) AS int_int_upto
            FROM `tabInterest Paid` ip
            WHERE ip.shipping_id = %s
              AND ip.date <= %s
            GROUP BY ip.shipping_id
        ) AS i
        ON n.shipping_id = i.shipping_id

        LEFT JOIN (
            SELECT  
                rd.shipping_id,
                SUM(drec.received) AS rec_amount,
                SUM(rd.bank_liability) AS bank_liab,
                MAX(rd.interest_upto_date) AS rec_int_upto,
                MAX(rd.interest_pct) AS rec_int_pct
            FROM `tabDoc Received Details` rd
            LEFT JOIN `tabDoc Received` drec ON drec.name= rd.inv_no
            WHERE rd.shipping_id = %s
              AND drec.received_date < %s
            GROUP BY rd.shipping_id
        ) AS rec_d
        ON n.shipping_id = rec_d.shipping_id


        LEFT JOIN (
            SELECT 
                dr.shipping_id,
                SUM(r.refund_amount) AS ref_amount, 
                MAX(dr.interest_upto_date) AS ref_int_upto, 
                MAX(dr.interest_pct) AS ref_int_pct
            FROM `tabDoc Refund Details` dr
            LEFT JOIN `tabDoc Refund` r ON r.name= dr.inv_no
            WHERE dr.shipping_id = %s
              AND r.refund_date < %s
            GROUP BY dr.shipping_id
        ) AS ref
        ON n.shipping_id = ref.shipping_id
    """

    params = (shipping_id, as_on, shipping_id, as_on, shipping_id, as_on, shipping_id, as_on)

    result = frappe.db.sql(query, params, as_dict=True)
    
    data= result[0] if result else {}

    data["rec_date"]=rec_date
    data["ref_date"]= ref_date
    data["rec_amount"]= rec_amount
    data["ref_amount"]= ref_amount
    data["bank_name"]= bank_name

    return data








