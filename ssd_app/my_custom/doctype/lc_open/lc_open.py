# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import pandas as pd
import numpy as np
import json
from ssd_app.utils.banking_line import check_banking_line, banking_lines_position
# from frappe.utils import today


def bank_line_validtation(doc):
    if not doc.amount:
        frappe.throw("❌ LC Amount cannot be empty. Please enter the amount.")

    company_code = frappe.db.get_value("Company", doc.company, "company_code")
    company_code=company_code.replace('.', '').replace('-', '').replace(' ', '_')
    bank_details = frappe.db.get_value("Bank", doc.bank, "bank")
    bank_details=bank_details.replace('.', '').replace('-', '').replace(' ', '_')
    payment_term= frappe.db.get_value("Payment Term", {"term_name":"LC Open"}, "name")
    bl_data=check_banking_line(doc.bank, doc.company, payment_term)
    bl = bl_data["balance_line"]
    if bl >= 0: #bl=-1 set for no limit
        if bl==0:
            frappe.throw("❌ No banking Line")
    
        if not doc.is_new():  # need to add logic here
            actual_lc_open = frappe.db.get_value("LC Open", doc.name, ["amount", "ex_rate"], as_dict=True)
            if round(doc.amount / doc.ex_rate, 2) > round(bl + (actual_lc_open.amount / actual_lc_open.ex_rate), 2):
                frappe.throw(f"""
                    ❌ <b>Nego amount exceeds Bank Line Limit.</b><br>
                    <b>Banking Line Balance:</b> {bl + (actual_lc_open.amount / actual_lc_open.ex_rate):,.2f}<br>
                    <b>Try to Entry:</b> {doc.amount / doc.ex_rate:,.2f}<br>
                """)

        elif (round(doc.amount / doc.ex_rate,2)) > bl:
            frappe.throw((f"""
            ❌ <b>LC amount exceeds Bank Line Limit.</b><br>
            <b>Banking Line Balance:</b> {bl:,.2f}<br>
            <b>Try to Entry:</b> {(doc.amount / doc.ex_rate):,.2f}<br>
        """))

class LCOpen(Document):
    def before_save(self):
        if self.company and self.bank:
            self.group_id = f"{self.company} : {self.bank}"

    def validate(self):
        bank_line_validtation(self)


# @frappe.whitelist()
# def import_bankingS(as_on, columns_order=[]):

#     data = import_banking_data(as_on)
#     if not data:
#         return "<p>No data found</p>"

#     df = pd.DataFrame(data)
#     if columns_order:
#         if isinstance(columns_order, str):
#             columns_order = json.loads(columns_order)
#     else:
#         columns_order = None  # No order specified
#         columns_order = sorted(df["p_term"].dropna().unique().tolist())
   
#     pivot = (
#         df.pivot_table(
#             index=["bank", "com"],
#             columns="p_term",
#             values="amount_usd",
#             aggfunc="sum",
#             fill_value=0.0
#         )
#         .reindex(columns=columns_order, fill_value=0.0)
#         .sort_index(level=[0, 1])
#     )

#     display_vals = pivot.replace(0.0, np.nan)

#     css = """
#         <style>
#         table.bank-summary { 
#             border-collapse: separate !important;
#             border-spacing: 0;
#             width: 100%; 
#             color:black;
#             font-family: Arial, sans-serif; 
#             font-size: 13px; 
#             border: 1px solid #ccc;
#             border-radius: 8px;
#             overflow: hidden;
#         }

#         .bank-summary th, .bank-summary td { 
#             border: 1px solid #ddd;
#             padding: 6px 10px; 
#         }

#         .bank-summary th { 
#             text-align: center; 
#             font-weight: bold;
#             color: white; 
#             white-space: nowrap;
#             background: linear-gradient(#4a6fa5, #3d5e8b); /* modern blue */
#             border-top: none;
#         }

#         .bank-summary th:first-child { border-top-left-radius: 8px; }
#         .bank-summary th:last-child { border-top-right-radius: 8px; }

        

#         .bank-summary td.num { text-align: right; white-space: nowrap; }
#         .bank-summary td.txt { text-align: left; }
#         .bank-summary td.blank { text-align: center; color: #555; }

#         /* New softer colors */
#         .bank-row-even { background-color: #f8fbff;}
#         .bank-row-odd  { background-color: #fdfcfb;}
#         .total { font-weight: bold; background-color: #d4f8d4; }
#         </style>
#         """

#     html = [css, '<table class="bank-summary">']
#     html.append("<thead><tr><th>Bank</th><th>Company</th>")
#     for col in columns_order:
#         html.append(f"<th>{col}</th>")
#     html.append("</tr></thead><tbody>")

#     # Grand totals
#     grand_totals = display_vals.copy().fillna(0.0).sum(axis=0)

#     # Bank colors
#     bank_colors = ["bank-row-even", "bank-row-odd"]
#     color_idx = 0

#     # Loop through banks
#     for bank, bank_frame in display_vals.groupby(level=0):
#         bank_rows = bank_frame.reset_index(level=0, drop=True)
#         rowspan = len(bank_rows)
#         first_row = True
#         row_class = bank_colors[color_idx % 2]
#         color_idx += 1

#         for company, row in bank_rows.iterrows():
#             html.append(f'<tr class="{row_class}">')
#             if first_row:
#                 html.append(f'<td class="txt" rowspan="{rowspan}">{bank}</td>')
#                 first_row = False
#             html.append(f'<td class="txt">{company}</td>')
#             for col in columns_order:
#                 val = row.get(col, np.nan)
#                 if pd.isna(val):
#                     html.append('<td class="blank">-</td>')
#                 else:
#                     html.append(f'<td class="num">{val:,.2f}</td>')
#             html.append("</tr>")

#     # Grand total row
#     html.append('<tr class="total"><td class="txt" colspan="2" style = "text-align: center; ">TOTAL</td>')
#     for col in columns_order:
#         tot = grand_totals.get(col, 0.0)
#         if tot == 0.0 or pd.isna(tot):
#             html.append('<td class="blank">-</td>')
#         else:
#             html.append(f'<td class="num">{tot:,.2f}</td>')
#     html.append("</tr>")

#     html.append("</tbody></table>")
#     return "".join(html)


@frappe.whitelist()
def banking_line():
    rows = frappe.db.get_all(
        "Bank Banking Line",
        filters={"banking_line": [">", 0]},
        fields=["name", "banking_line"]
    )

    banking_line_map = {r.name: r.banking_line for r in rows}
    total_line = sum(banking_line_map.values())


    css= """
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

      

        .bank-summary td.num { text-align: center; white-space: nowrap; }
        .bank-summary td.txt { text-align: left; }
        .bank-summary td.blank { text-align: center; color: #555; }

        /* New softer colors */
        .bank-row-even { background-color: #e6f0ff; }  /* soft, readable blue */
        .bank-row-odd  { background-color: #fff8e6; }  /* soft, readable cream */


        .total { font-weight: bold; background-color: #d4f8d4; }
        </style>
    """
    html=f"""
       <table class="bank-summary">
    <thead>
        <tr>
            <th>Bank</th>
            <th>Company</th>
            <th>Cash Loan</th>
            <th>Imp Loan</th>
            <th>LC Open</th>
            <th> DA</th>
            <th> DP</th>
        </tr>
    </thead>
    <tbody>
        <tr class="bank-row-even">
            <td class="txt" rowspan="2">CTBC</td>
            <td class="txt">GDI</td>
            <td class="num" rowspan="2">{0:,.0f}</td>
            <td class="num" colspan="2">{banking_line_map["bank_b_line-00003"]:,.0f}</td>
            <td class="num" rowspan="2" colspan="2">{0 :,.0f}</td>   
        </tr>
        <tr class="bank-row-even">
            <td class="txt">Tunwa Inds.</td>
            <td class="num" colspan="2">{banking_line_map["bank_b_line-00004"]:,.0f}</td>
        </tr>
      
        <tr class="bank-row-odd">
            <td class="txt" rowspan="3">CUB</td>
            <td class="txt">GDI</td>
            <td class="num" colspan="2" rowspan="3">{0:,.0f}</td>
            <td class="num" colspan="3" rowspan="3">{banking_line_map["bank_b_line-00007"]:,.0f}</td>
        </tr>
        <tr class="bank-row-odd">
            <td class="txt">Tunwa Inds.</td>
        </tr>
        <tr class="bank-row-odd">
            <td class="txt">UXL- Taiwan</td>
        </tr>
        <tr class="bank-row-even">
            <td class="txt" rowspan="2">SCSB</td>
            <td class="txt">GDI</td>
            <td class="num" rowspan="2">{0:,.0f}</td>
            <td class="num" colspan="4">{banking_line_map["bank_b_line-00010"]:,.0f}</td>       
        </tr>
        <tr class="bank-row-even">
            <td class="txt">Tunwa Inds.</td>
            <td class="num" colspan="4">{banking_line_map["bank_b_line-00011"]:,.0f}</td>
        </tr>
        <tr class="bank-row-odd">
            <td class="txt" rowspan="3">SINO</td>
            <td class="txt">GDI</td>
            <td class="num" rowspan="3">{banking_line_map["bank_b_line-00014"]:,.0f}</td>
            <td class="num" colspan="2" rowspan="2">{banking_line_map["bank_b_line-00015"]:,.0f}</td>
            <td class="num" colspan="2" rowspan="2">{banking_line_map["bank_b_line-00016"]:,.0f}</td>         
        </tr>
        <tr class="bank-row-odd">
            <td class="txt">Tunwa Inds.</td>
        </tr>
        <tr class="bank-row-odd">
            <td class="txt">UXL- Taiwan</td> 
            <td class="num" colspan="4">{0:,.0f}</td>
        </tr>
        <tr class="total">
            <td class="txt" colspan="2" style="text-align: center;">TOTAL</td>
            <td class="num" colspan="5">{total_line:,.0f}</td>
            
        </tr>
    </tbody>
</table>

"""
    html = [css, html]
    return "".join(html)

@frappe.whitelist()
def banking_line_balance():
    balance_banking_line = banking_lines_position()
    total_balance = sum(
            v["balance"]
            for v in balance_banking_line.values()
            if v["balance"] >= 0
        )
    print(balance_banking_line, total_balance)
    balance_banking=0
    css= """
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

      

        .bank-summary td.num { text-align: center; white-space: nowrap; }
        .bank-summary td.txt { text-align: left; }
        .bank-summary td.blank { text-align: center; color: #555; }

        /* New softer colors */
        .bank-row-even { background-color: #e6f0ff; }  /* soft, readable blue */
        .bank-row-odd  { background-color: #fff8e6; }  /* soft, readable cream */


        .total { font-weight: bold; background-color: #d4f8d4; }
        </style>
    """
    html=f"""
       <table class="bank-summary">
    <thead>
        <tr>
            <th>Bank</th>
            <th>Company</th>
            <th>Cash Loan</th>
            <th>Imp Loan</th>
            <th>LC Open</th>
            <th> DA</th>
            <th> DP</th>
        </tr>
    </thead>
    <tbody>
        <tr class="bank-row-even">
            <td class="txt" rowspan="2">CTBC</td>
            <td class="txt">GDI</td>
            <td class="num" rowspan="2">{balance_banking_line["bank_b_line-00002"]["balance"]:,.0f}</td>
            <td class="num" colspan="2">{balance_banking_line["bank_b_line-00003"]["balance"]:,.0f}</td>
            <td class="num" rowspan="2" colspan="2">{balance_banking_line["bank_b_line-00002"]["balance"]:,.0f}</td>   
        </tr>
        <tr class="bank-row-even">
            <td class="txt">Tunwa Inds.</td>
            <td class="num" colspan="2">{balance_banking_line["bank_b_line-00004"]["balance"]:,.0f}</td>
        </tr>
      
        <tr class="bank-row-odd">
            <td class="txt" rowspan="3">CUB</td>
            <td class="txt">GDI</td>
            <td class="num" colspan="2" rowspan="3">{balance_banking_line["bank_b_line-00005"]["balance"]:,.0f}</td>
            <td class="num" colspan="3" rowspan="3">{balance_banking_line["bank_b_line-00007"]["balance"]:,.0f}</td>
        </tr>
        <tr class="bank-row-odd">
            <td class="txt">Tunwa Inds.</td>
        </tr>
        <tr class="bank-row-odd">
            <td class="txt">UXL- Taiwan</td>
        </tr>
        <tr class="bank-row-even">
            <td class="txt" rowspan="2">SCSB</td>
            <td class="txt">GDI</td>
            <td class="num" rowspan="2">{balance_banking_line["bank_b_line-00009"]["balance"]:,.0f}</td>
            <td class="num" colspan="4">{balance_banking_line["bank_b_line-00010"]["balance"]:,.0f}</td>       
        </tr>
        <tr class="bank-row-even">
            <td class="txt">Tunwa Inds.</td>
            <td class="num" colspan="4">{balance_banking_line["bank_b_line-00011"]["balance"]:,.0f}</td>
        </tr>
        <tr class="bank-row-odd">
            <td class="txt" rowspan="3">SINO</td>
            <td class="txt">GDI</td>
            <td class="num" rowspan="3">{balance_banking_line["bank_b_line-00014"]["balance"]:,.0f}</td>
            <td class="num" colspan="2" rowspan="2">{balance_banking_line["bank_b_line-00015"]["balance"]:,.0f}</td>
            <td class="num" colspan="2" rowspan="2">{balance_banking_line["bank_b_line-00016"]["balance"]:,.0f}</td>         
        </tr>
        <tr class="bank-row-odd">
            <td class="txt">Tunwa Inds.</td>
            
        </tr>
        <tr class="bank-row-odd">
            <td class="txt">UXL- Taiwan</td> 
            <td class="num" colspan="4">{balance_banking_line["bank_b_line-00013"]["balance"]:,.0f}</td>
        </tr>
        <tr class="total">
            <td class="txt" colspan="2" style="text-align: center;">TOTAL</td>
            <td class="num" colspan="5">{total_balance:,.0f}</td>
            
        </tr>
    </tbody>
</table>

"""
    html = [css, html]
    return "".join(html)


