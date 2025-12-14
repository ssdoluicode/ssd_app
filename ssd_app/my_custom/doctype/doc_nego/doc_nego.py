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


from ssd_app.utils.banking import export_banking_data, balance_banking_line_data, check_banking_line, import_banking_data


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
    invoice = frappe.db.get_value("CIF Sheet", doc.inv_no, "inv_no")
    doc.custom_title = f"{doc.name} ({invoice})".strip()
    doc.invoice_no = invoice
    doc.cif_id= doc.inv_no

   

def final_validation(doc):
    if not doc.inv_no:
        return

    # Fetch CIF document value
    cif_data = frappe.db.get_value("CIF Sheet", doc.inv_no, ["document", "inv_date", "bank"], as_dict=True)
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


def bank_line_validtation(doc):
    result = frappe.db.get_value("CIF Sheet", doc.inv_no, ["shipping_company", "bank", "payment_term"] , as_dict=True)
   
    shipping_company = result["shipping_company"]
    bank = result["bank"]
    payment_term = result["payment_term"]
    company_code = frappe.db.get_value("Company", shipping_company, "company_code")
    company_code=company_code.replace('.', '').replace('-', '').replace(' ', '_')
    bank_details = frappe.db.get_value("Bank", bank, "bank")
    bank_details=bank_details.replace('.', '').replace('-', '').replace(' ', '_')
    bl = check_banking_line(company_code, bank_details, payment_term)

    if payment_term == "DA" or payment_term == "DP":
        if bl== None:
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

class DocNego(Document): 
    def validate(self):
        final_validation(self)
        update_cif_bank_if_missing(self)
        bank_line_validtation(self)
        calculate_term_days(self)
        calculate_due_date

    
    def before_save(self):
        put_value_from_cif(self)
        set_calculated_fields(self)
    
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
def used_banking_line(as_on, columns_order=[]):
    # columns_order = ["LC", "LC at Sight", "DA", "DP", "Cash Loan", "Imp Loan", "LC Open", "Usance LC"] 
    imp_data = import_banking_data(as_on)
    exp_data = export_banking_data(as_on)
    if not imp_data:
        return "<p>No data found</p>"

    imp_df = pd.DataFrame(imp_data)
    exp_df= pd.DataFrame(exp_data)
    exp_df = exp_df.rename(columns={
            "inv_no": "ref_no",
            "nego": "amount_usd"
        })
    
    df = pd.concat([imp_df, exp_df], ignore_index=True)
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
            values="amount_usd",
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




@frappe.whitelist()
def update_export_due_date(docname, new_due_date, due_date_confirm, note= None):
    """Update due date and confirmation flag"""
    # frappe.db.set_value("Doc Nego", docname, "bank_due_date", new_due_date)
    # frappe.db.set_value("Doc Nego", docname, "due_date_confirm", due_date_confirm)
    # frappe.db.set_value("Doc Nego", docname, "note", note)
    frappe.db.set_value("Doc Nego", docname, {
        "bank_due_date": new_due_date,
        "due_date_confirm": int(due_date_confirm),
        "note": note or ""
    })
    return "success"




@frappe.whitelist()
def update_import_due_date(doctype_name,docname, new_due_date, due_date_confirm, note=None):
    """Update due date and confirmation flag"""
    # frappe.db.set_value("Doc Nego", docname, "bank_due_date", new_due_date)
    # frappe.db.set_value("Doc Nego", docname, "due_date_confirm", due_date_confirm)
    # frappe.db.set_value("Doc Nego", docname, "note", note)
    frappe.db.set_value(doctype_name, docname, {
        "due_date": new_due_date,
        "due_date_confirm": int(due_date_confirm),
        "note": note or ""
    })
    return "success"


@frappe.whitelist()
def get_cif_summary(id_name, id, as_on= None):
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
        cif_id = frappe.db.get_value("Doc Nego", id, "cif_id")
        bank = frappe.db.get_value("CIF Sheet", cif_id, "bank")
        bank_name = frappe.db.get_value("Bank", bank, "bank")

    elif id_name == "rec":
        data = frappe.db.get_value("Doc Received",id,["cif_id", "received_date", "received"],as_dict=True)
        cif_id = data.cif_id
        rec_date = data.received_date
        rec_amount = data.received
        as_on= data.received_date
        bank = frappe.db.get_value("CIF Sheet", cif_id, "bank")
        bank_name = frappe.db.get_value("Bank", bank, "bank")

    elif id_name == "ref":
        data = frappe.db.get_value("Doc Refund",id,["cif_id", "refund_date", "refund_amount"],as_dict=True)
        cif_id = data.cif_id
        ref_date = data.refund_date
        ref_amount = data.refund_amount
        as_on= data.refund_date
        bank = frappe.db.get_value("CIF Sheet", cif_id, "bank")
        bank_name = frappe.db.get_value("Bank", bank, "bank")

    query = f"""
        SELECT
            n.cif_id,
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
                nd.cif_id,
                SUM(nd.nego_amount) AS nego_amount,
                MAX(nd.nego_date) AS nego_date,
                MAX(nd.interest_upto_date) AS nego_int_upto,
                MAX(nd.interest_pct) AS nego_int_pct
            FROM `tabDoc Nego Details` nd
            WHERE nd.cif_id = %s
              AND nd.nego_date < %s
            GROUP BY nd.cif_id
        ) AS n

        LEFT JOIN (
            SELECT
                ip.cif_id,
                MAX(ip.interest_rate) AS int_int_pct,
                MAX(ip.interest_upto_date) AS int_int_upto
            FROM `tabInterest Paid` ip
            WHERE ip.cif_id = %s
              AND ip.date <= %s
            GROUP BY ip.cif_id
        ) AS i
        ON n.cif_id = i.cif_id

        LEFT JOIN (
            SELECT  
                rd.cif_id,
                SUM(rd.received_amount) AS rec_amount,
                SUM(rd.bank_liability) AS bank_liab,
                MAX(rd.interest_upto_date) AS rec_int_upto,
                MAX(rd.interest_pct) AS rec_int_pct
            FROM `tabDoc Received Details` rd
            WHERE rd.cif_id = %s
              AND rd.received_date < %s
            GROUP BY rd.cif_id
        ) AS rec_d
        ON n.cif_id = rec_d.cif_id


        LEFT JOIN (
            SELECT 
                dr.cif_id,
                SUM(dr.refund_amount) AS ref_amount, 
                MAX(dr.interest_upto_date) AS ref_int_upto, 
                MAX(dr.interest_pct) AS ref_int_pct
            FROM `tabDoc Refund Details` dr
            WHERE dr.cif_id = %s
              AND dr.refund_date < %s
            GROUP BY dr.cif_id
        ) AS ref
        ON n.cif_id = ref.cif_id
    """

    params = (cif_id, as_on, cif_id, as_on, cif_id, as_on, cif_id, as_on)

    result = frappe.db.sql(query, params, as_dict=True)
    
    data= result[0] if result else {}

    data["rec_date"]=rec_date
    data["ref_date"]= ref_date
    data["rec_amount"]= rec_amount
    data["ref_amount"]= ref_amount
    data["bank_name"]= bank_name

    return data








