# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import pandas as pd

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
def import_banking_line(as_on):
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
    # Force to list of pure dicts
    data = [dict(row) for row in rows]

    if not data:
        return "<p>No data found</p>"

    df = pd.DataFrame(data)

    # Get full list of banks across all data
    all_banks = sorted(df['bank'].dropna().unique())

    total_columns = 1 + len(all_banks) + 1
    col_width = 100 / total_columns

    html = """
    <style>
        .babking_line-table-container {
            max-height: 80vh;
            overflow: auto;
            width: 100%;
        }
        table.babking_line-table {
            border-collapse: collapse;
            width: 100%;
            font-size: 13px;
        }
        table.babking_line-table th, table.babking_line-table td {
            border: 1px solid #ddd;
            padding: 6px;
            text-align: right;
            white-space: nowrap;
        }
        table.babking_line-table th {
            background-color: #f5f5f5;
            position: sticky;
            top: 0;
            z-index: 1;
            text-align: center;
        }
        h3{
            margin-top: 10px;
            margin-bottom: 0px;

        }
        td#left { text-align: left; }
        .total-column { font-weight: bold; }
        .total-row td { font-weight: bold; }
    </style>
    """

    col_width = 15  # percent for Payment Term column
    num_numeric_cols = len(all_banks) + 1  # +1 for Total column
    numeric_col_width = (100 - col_width) / num_numeric_cols

    # Process per company
    com_list = df['com'].dropna().unique()
    for com in com_list:
        df_com = df[df['com'] == com]
        pivot = pd.pivot_table(
            df_com, values='amount_usd', index='p_term', columns='bank',
            aggfunc='sum', fill_value=0
        )
        pivot = pivot.reindex(columns=all_banks, fill_value=0)
        pivot['Total'] = pivot.sum(axis=1)
        total_row = pd.DataFrame(pivot.sum(axis=0)).T
        total_row.index = ['Total']
        pivot = pd.concat([pivot, total_row])
        pivot = pivot.round(2)

        html += f"<h3>{com}</h3>"
        html += "<div class='babking_line-table-container'>"
        html += "<table class='babking_line-table'>"
        html += "<thead><tr>"
        html += f"<th id='left' style='width:{col_width:.2f}%;'>Payment Term</th>"
        for bank in all_banks:
            html += f"<th style='width:{numeric_col_width:.2f}%;'>{bank}</th>"
        html += f"<th style='width:{numeric_col_width:.2f}%;'>Total</th></tr></thead>"
        html += "<tbody>"

        for idx, row in pivot.iterrows():
            total_row_class = "total-row" if idx == 'Total' else ""
            html += f"<tr class='{total_row_class}'><td id='left'>{idx}</td>"
            for bank in all_banks:
                html += f"<td>{'{:,.2f}'.format(row[bank])}</td>"
            html += f"<td class='total-column'>{'{:,.2f}'.format(row['Total'])}</td></tr>"
        html += "</tbody></table></div>"

    # Grand total
    grand_pivot = pd.pivot_table(
        df, values='amount_usd', index='p_term', columns='bank',
        aggfunc='sum', fill_value=0
    )
    grand_pivot = grand_pivot.reindex(columns=all_banks, fill_value=0)
    grand_pivot['Total'] = grand_pivot.sum(axis=1)
    total_row = pd.DataFrame(grand_pivot.sum(axis=0)).T
    total_row.index = ['Total']
    grand_pivot = pd.concat([grand_pivot, total_row])
    grand_pivot = grand_pivot.round(2)

    html += "<h3>All Companies</h3>"
    html += "<div class='babking_line-table-container'>"
    html += "<table class='babking_line-table'>"
    html += "<thead><tr>"
    html += f"<th id='left' style='width:{col_width:.2f}%;'>Payment Term</th>"
    for bank in all_banks:
        html += f"<th style='width:{numeric_col_width:.2f}%;'>{bank}</th>"
    html += f"<th style='width:{numeric_col_width:.2f}%;'>Total</th></tr></thead>"
    html += "<tbody>"

    for idx, row in grand_pivot.iterrows():
        total_row_class = "total-row" if idx == 'Total' else ""
        html += f"<tr class='{total_row_class}'><td id='left'>{idx}</td>"
        for bank in all_banks:
            html += f"<td>{'{:,.2f}'.format(row[bank])}</td>"
        html += f"<td class='total-column'>{'{:,.2f}'.format(row['Total'])}</td></tr>"

    html += "</tbody></table></div>"

    return html