# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import pandas as pd
import numpy as np
import json
from ssd_app.utils.banking import export_banking_data, import_banking_data, banking_line_data
from datetime import date
today = date.today() 


def final_validation(doc):
    if not doc.amount:
        frappe.throw("❌ LC Amount cannot be empty. Please enter the amount.")

class LCOpen(Document):
    def before_save(self):
        if self.amount and self.ex_rate:
            self.amount_usd = round(self.amount / self.ex_rate, 2)
    def validate(self):
	    final_validation(self)



@frappe.whitelist()
def import_banking(as_on, columns_order=[]):

    data = import_banking_data(as_on)
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
def banking_line():
    data= banking_line_data()
    total_line = sum(data.values())
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
            <th> DA</th>
        </tr>
    </thead>
    <tbody>
        <tr class="bank-row-even">
            <td class="txt" rowspan="2">CTBC</td>
            <td class="txt">GDI</td>
            <td class="num" rowspan="2">{data["line_0"]:,.0f}</td>
            <td class="num" colspan="2">{data["ctbc_imp_lc_8"]:,.0f}</td>
            <td class="num" rowspan="2" colspan="2">{data["line_0"] :,.0f}</td>   
        </tr>
        <tr class="bank-row-even">
            <td class="txt">Tunwa Inds.</td>
            <td class="num" colspan="2">{data["ctbc_imp_lc_3"]:,.0f}</td>
        </tr>
      
        <tr class="bank-row-odd">
            <td class="txt" rowspan="3">CUB</td>
            <td class="txt">GDI</td>
            <td class="num" colspan="2" rowspan="3">{data["line_0"]:,.0f}</td>
            <td class="num" colspan="3" rowspan="3">{data["cub_lc_da_dp"]:,.0f}</td>
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
            <td class="num" rowspan="2">{data["line_0"]:,.0f}</td>
            <td class="num" colspan="4">{data["scsb_imp_lc_da_dp_8"]:,.0f}</td>       
        </tr>
        <tr class="bank-row-even">
            <td class="txt">Tunwa Inds.</td>
            <td class="num" colspan="4">{data["scsb_imp_lc_da_dp_3"]:,.0f}</td>
        </tr>
        <tr class="bank-row-odd">
            <td class="txt" rowspan="3">SINO</td>
            <td class="txt">GDI</td>
            <td class="num" rowspan="3">{data["sino_cln"]:,.0f}</td>
            <td class="num" colspan="2">{data["sino_imp_lc_8"]:,.0f}</td>
            <td class="num" colspan="2">{data["sino_da_dp_8"]:,.0f}</td>         
        </tr>
        <tr class="bank-row-odd">
            <td class="txt">Tunwa Inds.</td>
            <td class="num" colspan="2">{data["sino_imp_lc_3"]:,.0f}</td>
            <td class="num" colspan="2">{data["sino_da_dp_3"]:,.0f}</td>
        </tr>
        <tr class="bank-row-odd">
            <td class="txt">UXL- Taiwan</td> 
            <td class="num" colspan="4">{data["line_0"]:,.0f}</td>
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
    banking_line= banking_line_data()
    ctbc_imp_lc_8= banking_line["ctbc_imp_lc_8"]
    ctbc_imp_lc_3= banking_line["ctbc_imp_lc_3"]
    cub_lc_da_dp=banking_line["cub_lc_da_dp"]
    scsb_imp_lc_da_dp_8=banking_line["scsb_imp_lc_da_dp_8"]
    scsb_imp_lc_da_dp_3=banking_line["scsb_imp_lc_da_dp_3"]
    sino_cln=banking_line["sino_cln"]
    sino_imp_lc_8=banking_line["sino_imp_lc_8"]
    sino_da_dp_8=banking_line["sino_da_dp_8"]
    sino_imp_lc_3=banking_line["sino_imp_lc_3"]
    sino_da_dp_3=banking_line["sino_da_dp_3"]


    export_banking=export_banking_data(today)
    export_banking_result = {}
    for row in export_banking:
        bank=row['bank'].replace('.', '').replace('-', '').replace(' ', '_')
        com= row['com'].replace('.', '').replace('-', '').replace(' ', '_')
        p_term=row['p_term'].replace('.', '').replace('-', '').replace(' ', '_')
        key = f"{bank}_{com}_{p_term}"
        export_banking_result[key] = export_banking_result.get(key, 0) + row['document']
    
    e_ctbc_da_8 = export_banking_result.get("CTBC_GDI_DA", 0)
    e_cub_da_8  = export_banking_result.get("CUB_GDI_DA", 0)
    e_scsb_da_8 = export_banking_result.get("SCSB_GDI_DA", 0)
    e_sino_da_8 = export_banking_result.get("SINO_GDI_DA", 0)
    e_ctbc_dp_8 = export_banking_result.get("CTBC_GDI_DP", 0)
    e_cub_dp_8  = export_banking_result.get("CUB_GDI_DP", 0)
    e_scsb_dp_8 = export_banking_result.get("SCSB_GDI_DP", 0)
    e_sino_dp_8 = export_banking_result.get("SINO_GDI_DP", 0)

    e_ctbc_da_3 = export_banking_result.get("CTBC_Tunwa_Inds_DA", 0)
    e_cub_da_3 = export_banking_result.get("CUB_Tunwa_Inds_DA", 0)
    e_scsb_da_3 = export_banking_result.get("SCSB_Tunwa_Inds_DA", 0)
    e_sino_da_3 = export_banking_result.get("SINO_Tunwa_Inds_DA", 0)
    e_ctbc_dp_3 = export_banking_result.get("CTBC_Tunwa_Inds_DP", 0)
    e_cub_dp_3 = export_banking_result.get("CUB_Tunwa_Inds_DP", 0)
    e_scsb_dp_3 = export_banking_result.get("SCSB_Tunwa_Inds_DP", 0)
    e_sino_dp_3 = export_banking_result.get("SINO_Tunwa_Inds_DP", 0)

    e_ctbc_da_2 = export_banking_result.get("CTBC_UXL_Taiwan_DA", 0)
    e_cub_da_2 = export_banking_result.get("CUB_UXL_Taiwan_DA", 0)
    e_scsb_da_2 = export_banking_result.get("SCSB_UXL_Taiwan_DA", 0)
    e_sino_da_2 = export_banking_result.get("SINO_UXL_Taiwan_DA", 0)
    e_ctbc_dp_2 = export_banking_result.get("CTBC_UXL_Taiwan_DP", 0)
    e_cub_dp_2 = export_banking_result.get("CUB_UXL_Taiwan_DP", 0)
    e_scsb_dp_2 = export_banking_result.get("SCSB_UXL_Taiwan_DP", 0)
    e_sino_dp_2 = export_banking_result.get("SINO_UXL_Taiwan_DP", 0)

    import_banking=import_banking_data(today)
    import_banking_result = {}
    for row in import_banking:
        bank=row['bank'].replace('.', '').replace('-', '').replace(' ', '_')
        com= row['com'].replace('.', '').replace('-', '').replace(' ', '_')
        p_term=row['p_term'].replace('.', '').replace('-', '').replace(' ', '_')
        key = f"{bank}_{com}_{p_term}"
        import_banking_result[key] = import_banking_result.get(key, 0) + row['amount_usd']


    i_ctbc_lc_8 = import_banking_result.get("CTBC_GDI_LC_Open", 0) + import_banking_result.get("CTBC_GDI_Usance_LC", 0)
    i_cub_lc_8  = import_banking_result.get("CUB_GDI_LC_Open", 0) + import_banking_result.get("CUB_GDI_Usance_LC", 0)
    i_scsb_lc_8 = import_banking_result.get("SCSB_GDI_LC_Open", 0) + import_banking_result.get("SCSB_GDI_Usance_LC", 0)
    i_sino_lc_8 = import_banking_result.get("SINO_GDI_LC_Open", 0) + import_banking_result.get("SINO_GDI_Usance_LC", 0)
    i_ctbc_imp_8 = import_banking_result.get("CTBC_GDI_Imp_Loan", 0)
    # i_cub_imp_8  = import_banking_result.get("CUB_GDI_Imp_Loan", 0)
    i_scsb_imp_8 = import_banking_result.get("SCSB_GDI_Imp_Loan", 0)
    i_sino_imp_8 = import_banking_result.get("SINO_GDI_Imp_Loan", 0)
    # i_ctbc_cash_8 = import_banking_result.get("CTBC_GDI_Cash_Loan", 0)
    # i_cub_cash_8  = import_banking_result.get("CUB_GDI_Cash_Loan", 0)
    # i_scsb_cash_8 = import_banking_result.get("SCSB_GDI_Cash_Loan", 0)
    i_sino_cash_8 = import_banking_result.get("SINO_GDI_Cash_Loan", 0)

    i_ctbc_lc_3 = import_banking_result.get("CTBC_Tunwa_Inds_LC_Open", 0) + import_banking_result.get("CTBC_Tunwa_Inds_Usance_LC", 0)
    i_cub_lc_3 = import_banking_result.get("CUB_Tunwa_Inds_LC_Open", 0) + import_banking_result.get("CUB_Tunwa_Inds_Usance_LC", 0)
    i_scsb_lc_3 = import_banking_result.get("SCSB_Tunwa_Inds_LC_Open", 0) + import_banking_result.get("SCSB_Tunwa_Inds_Usance_LC", 0)
    i_sino_lc_3 = import_banking_result.get("SINO_Tunwa_Inds_LC_Open", 0) + import_banking_result.get("SINO_Tunwa_Inds_Usance_LC", 0)
    i_ctbc_imp_3 = import_banking_result.get("CTBC_Tunwa_Inds_Imp_Loan", 0)
    # i_cub_imp_3 = import_banking_result.get("CUB_Tunwa_Inds_Imp_Loan", 0)
    i_scsb_imp_3 = import_banking_result.get("SCSB_Tunwa_Inds_Imp_Loan", 0)
    i_sino_imp_3 = import_banking_result.get("SINO_Tunwa_Inds_Imp_Loan", 0)
    # i_ctbc_cash_3 = import_banking_result.get("CTBC_Tunwa_Inds_Cash_Loan", 0)
    # i_cub_cash_3 = import_banking_result.get("CUB_Tunwa_Inds_Cash_Loan", 0)
    # i_scsb_cash_3 = import_banking_result.get("SCSB_Tunwa_Inds_Cash_Loan", 0)
    i_sino_cash_3 = import_banking_result.get("SINO_Tunwa_Inds_Cash_Loan", 0)

    # i_ctbc_lc_2 = import_banking_result.get("CTBC_UXL_Taiwan_LC_Open", 0) + import_banking_result.get("CTBC_UXL_Taiwan_Usance_LC", 0)
    i_cub_lc_2 = import_banking_result.get("CUB_UXL_Taiwan_LC_Open", 0) + import_banking_result.get("CUB_UXL_Taiwan_Usance_LC", 0)
    # i_scsb_lc_2 = import_banking_result.get("SCSB_UXL_Taiwan_LC_Open", 0) + import_banking_result.get("SCSB_UXL_Taiwan_Usance_LC", 0)
    # i_sino_lc_2 = import_banking_result.get("SINO_UXL_Taiwan_LC_Open", 0) + import_banking_result.get("SINO_UXL_Taiwan_Usance_LC", 0)
    # i_ctbc_imp_2 = import_banking_result.get("CTBC_UXL_Taiwan_Imp_Loan", 0)
    # i_cub_imp_2 = import_banking_result.get("CUB_UXL_Taiwan_Imp_Loan", 0)
    # i_scsb_imp_2 = import_banking_result.get("SCSB_UXL_Taiwan_Imp_Loan", 0)
    # i_sino_imp_2 = import_banking_result.get("SINO_UXL_Taiwan_Imp_Loan", 0)
    # i_ctbc_cash_2 = import_banking_result.get("CTBC_UXL_Taiwan_Cash_Loan", 0)
    # i_cub_cash_2 = import_banking_result.get("CUB_UXL_Taiwan_Cash_Loan", 0)
    # i_scsb_cash_2 = import_banking_result.get("SCSB_UXL_Taiwan_Cash_Loan", 0)
    i_sino_cash_2 = import_banking_result.get("SINO_UXL_Taiwan_Cash_Loan", 0)


    u_ctbc_imp_lc_8= i_ctbc_imp_8 + i_ctbc_lc_8
    u_ctbc_imp_lc_3= i_ctbc_imp_3 + i_ctbc_lc_3
    u_cub_lc_da_dp= i_cub_lc_8 + i_cub_lc_3 + i_cub_lc_2 + e_cub_dp_8 +e_cub_dp_3+e_cub_dp_2 + e_cub_da_8 +e_cub_da_3+e_cub_da_2
    u_scsb_imp_lc_da_dp_8= i_scsb_lc_8 + i_scsb_imp_8 + e_scsb_dp_8 + e_scsb_da_8
    u_scsb_imp_lc_da_dp_3=i_scsb_lc_3 + i_scsb_imp_3 + e_scsb_dp_3 + e_scsb_da_3
    u_sino_cln=i_sino_cash_8 + i_sino_cash_3 +i_sino_cash_2
    u_sino_imp_lc_8=i_sino_lc_8 + i_sino_imp_8
    u_sino_da_dp_8= e_sino_dp_8 + e_sino_da_8
    u_sino_imp_lc_3=i_sino_lc_3 + i_sino_imp_3
    u_sino_da_dp_3=e_sino_dp_3 + e_sino_da_3


    b_ctbc_imp_lc_8 = ctbc_imp_lc_8 - u_ctbc_imp_lc_8
    b_ctbc_imp_lc_3 = ctbc_imp_lc_3 - u_ctbc_imp_lc_3
    b_cub_lc_da_dp = cub_lc_da_dp - u_cub_lc_da_dp
    b_scsb_imp_lc_da_dp_8 = scsb_imp_lc_da_dp_8 - u_scsb_imp_lc_da_dp_8
    b_scsb_imp_lc_da_dp_3 = scsb_imp_lc_da_dp_3 - u_scsb_imp_lc_da_dp_3
    b_sino_cln = sino_cln - u_sino_cln
    b_sino_imp_lc_8 = sino_imp_lc_8 - u_sino_imp_lc_8
    b_sino_da_dp_8 = sino_da_dp_8 - u_sino_da_dp_8
    b_sino_imp_lc_3 = sino_imp_lc_3 - u_sino_imp_lc_3
    b_sino_da_dp_3 = sino_da_dp_3 - u_sino_da_dp_3

    total_balance = (
        b_ctbc_imp_lc_8 + b_ctbc_imp_lc_3 + b_cub_lc_da_dp + b_scsb_imp_lc_da_dp_8 + b_scsb_imp_lc_da_dp_3 +
        b_sino_cln + b_sino_imp_lc_8 + b_sino_da_dp_8 + b_sino_imp_lc_3 + b_sino_da_dp_3
    )
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
            <th> DA</th>
        </tr>
    </thead>
    <tbody>
        <tr class="bank-row-even">
            <td class="txt" rowspan="2">CTBC</td>
            <td class="txt">GDI</td>
            <td class="num" rowspan="2">{0:,.0f}</td>
            <td class="num" colspan="2">{b_ctbc_imp_lc_8:,.0f}</td>
            <td class="num" rowspan="2" colspan="2">{0 :,.0f}</td>   
        </tr>
        <tr class="bank-row-even">
            <td class="txt">Tunwa Inds.</td>
            <td class="num" colspan="2">{b_ctbc_imp_lc_3:,.0f}</td>
        </tr>
      
        <tr class="bank-row-odd">
            <td class="txt" rowspan="3">CUB</td>
            <td class="txt">GDI</td>
            <td class="num" colspan="2" rowspan="3">{0:,.0f}</td>
            <td class="num" colspan="3" rowspan="3">{b_cub_lc_da_dp:,.0f}</td>
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
            <td class="num" colspan="4">{b_scsb_imp_lc_da_dp_8:,.0f}</td>       
        </tr>
        <tr class="bank-row-even">
            <td class="txt">Tunwa Inds.</td>
            <td class="num" colspan="4">{b_scsb_imp_lc_da_dp_3:,.0f}</td>
        </tr>
        <tr class="bank-row-odd">
            <td class="txt" rowspan="3">SINO</td>
            <td class="txt">GDI</td>
            <td class="num" rowspan="3">{b_sino_cln:,.0f}</td>
            <td class="num" colspan="2">{b_sino_imp_lc_8:,.0f}</td>
            <td class="num" colspan="2">{b_sino_da_dp_8:,.0f}</td>         
        </tr>
        <tr class="bank-row-odd">
            <td class="txt">Tunwa Inds.</td>
            <td class="num" colspan="2">{b_sino_imp_lc_3:,.0f}</td>
            <td class="num" colspan="2">{b_sino_da_dp_3:,.0f}</td>
        </tr>
        <tr class="bank-row-odd">
            <td class="txt">UXL- Taiwan</td> 
            <td class="num" colspan="4">{0:,.0f}</td>
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


