# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import pandas as pd
import numpy as np
import json



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
def import_banking_line(as_on, columns_order=[]):
    query = """
    SELECT *
    FROM (
        -- LC Open
        SELECT 
            lc_o.name, 
            lc_o.lc_no AS ref_no,
            com.company_code AS com,
            bank.bank AS bank,
            'LC Open' AS p_term,
            0 AS document,
            ROUND(IF(
                lc_o.amount 
                - IFNULL(lc_p.lc_p_amount, 0) 
                - IFNULL(imp_loan.imp_loan_amount, 0) 
                - IFNULL(u_lc.u_lc_amount, 0) 
                < lc_o.amount * lc_o.tolerance / 100,
                0,
                lc_o.amount 
                - IFNULL(lc_p.lc_p_amount, 0) 
                - IFNULL(imp_loan.imp_loan_amount, 0) 
                - IFNULL(u_lc.u_lc_amount, 0)
            ) / lc_o.ex_rate,2
        ) AS amount_usd
        FROM `tabLC Open` lc_o
        LEFT JOIN `tabSupplier` sup 
            ON sup.name = lc_o.supplier
        LEFT JOIN `tabBank` bank 
            ON bank.name = lc_o.bank
        LEFT JOIN (
            SELECT lc_no, SUM(amount) AS lc_p_amount 
            FROM `tabLC Payment`
            GROUP BY lc_no
        ) lc_p 
            ON lc_p.lc_no = lc_o.name
        LEFT JOIN (
            SELECT lc_no, SUM(loan_amount) AS imp_loan_amount 
            FROM `tabImport Loan`
            GROUP BY lc_no
        ) imp_loan 
            ON imp_loan.lc_no = lc_o.name
        LEFT JOIN (
            SELECT lc_no, SUM(usance_lc_amount) AS u_lc_amount 
            FROM `tabUsance LC`
            GROUP BY lc_no
        ) u_lc 
            ON u_lc.lc_no = lc_o.name
        LEFT JOIN `tabCompany` com ON lc_o.company= com.name

        UNION ALL

        -- Import Loan
        SELECT 
            imp_l.name, 
            imp_l.inv_no AS ref_no,
            com.company_code AS com,
            bank.bank AS bank,
            'Imp Loan' AS p_term,
            0 AS document,
            ROUND(IFNULL(
                imp_l.loan_amount - IFNULL(imp_l_p.imp_l_p_amount, 0), 
                0
            ) / lc_o.ex_rate,2
        ) AS amount_usd
        FROM `tabImport Loan` imp_l
        LEFT JOIN `tabLC Open` lc_o 
            ON imp_l.lc_no = lc_o.name
        LEFT JOIN `tabSupplier` sup 
            ON sup.name = lc_o.supplier
        LEFT JOIN `tabBank` bank 
            ON bank.name = lc_o.bank
        LEFT JOIN (
            SELECT inv_no, SUM(amount) AS imp_l_p_amount
            FROM `tabImport Loan Payment` 
            GROUP BY inv_no
        ) imp_l_p 
            ON imp_l_p.inv_no = imp_l.name
        LEFT JOIN `tabCompany` com ON lc_o.company= com.name
            
        UNION ALL   
            
        SELECT 
                u_lc.name, 
                u_lc.inv_no AS ref_no,
                com.company_code AS com,
                bank.bank AS bank,
                'Usance LC' AS p_term,
                0 AS document,
                ROUND(IFNULL(u_lc.usance_lc_amount - IFNULL(u_lc_p.u_lc_p_amount, 0), 0)/ lc_o.ex_rate,2) AS amount_usd
            FROM `tabUsance LC` u_lc
            LEFT JOIN `tabLC Open` lc_o ON u_lc.lc_no = lc_o.name
            LEFT JOIN `tabSupplier` sup ON sup.name = lc_o.supplier
            LEFT JOIN `tabBank` bank ON bank.name = lc_o.bank
            LEFT JOIN (
                SELECT inv_no, SUM(amount) AS u_lc_p_amount
                FROM `tabUsance LC Payment` 
                GROUP BY inv_no
            ) u_lc_p ON u_lc_p.inv_no = u_lc.name
            LEFT JOIN `tabCompany` com ON lc_o.company= com.name
        
    UNION ALL
    
    SELECT 
                c_loan.name, 
                c_loan.cash_loan_no AS ref_no,
                com.company_code AS com,
                bank.bank AS bank,
                'Cash Loan' AS p_term,
                0 AS document,
                ROUND(IFNULL(c_loan.cash_loan_amount - IFNULL(c_loan_p.c_loan_p_amount, 0), 0) / c_loan.ex_rate,2
        ) AS amount_usd
            FROM `tabCash Loan` c_loan
            LEFT JOIN `tabBank` bank ON bank.name = c_loan.bank
            LEFT JOIN (
                SELECT cash_loan_no, SUM(amount) AS c_loan_p_amount
                FROM `tabCash Loan Payment` 
                GROUP BY cash_loan_no
            ) c_loan_p ON c_loan_p.cash_loan_no = c_loan.name
            LEFT JOIN `tabCompany` com ON c_loan.company= com.name
            
    ) AS combined
    WHERE amount_usd > 0;
    """
    
    rows = frappe.db.sql(query, {"as_on": as_on}, as_dict=True)
    if not rows:
        return "<p>No data found</p>"

    data = [dict(r) for r in rows]
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
            border-collapse: collapse; 
            width: 100%; 
            font-family: Arial, sans-serif; 
            font-size: 13px; 
        }
        .bank-summary th, .bank-summary td { 
            border: 1px solid #000; 
            padding: 6px 10px; 
        }
        .bank-summary th { 
            text-align: center; 
            font-weight: bold; 
            background-color: #f5f5f5; 
        }
        .bank-summary td.num { text-align: right; white-space: nowrap; }
        .bank-summary td.txt { text-align: left; }
        .bank-summary td.blank { text-align: center; color: #555; }
        
        .bank-row-even { background-color: #eaf2ff; }  /* light blue */
        .bank-row-odd  { background-color: #fff4e5; }  /* light orange */
        .total { font-weight: bold; background-color: #c6efce; } /* light green */

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
    html.append('<tr class="total"><td class="txt" colspan="2">TOTAL</td>')
    for col in columns_order:
        tot = grand_totals.get(col, 0.0)
        if tot == 0.0 or pd.isna(tot):
            html.append('<td class="blank">-</td>')
        else:
            html.append(f'<td class="num">{tot:,.2f}</td>')
    html.append("</tr>")

    html.append("</tbody></table>")
    return "".join(html)
