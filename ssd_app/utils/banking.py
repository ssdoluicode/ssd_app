import frappe

@frappe.whitelist()
def banking_line_data():

    ctbc_imp_lc_8=2000000
    ctbc_imp_lc_3=1000000
    cub_lc_da_dp=8000000
    scsb_imp_lc_da_dp_8=3000000
    scsb_imp_lc_da_dp_3=500000
    sino_cln= 1050000
    sino_imp_lc_8=1100000
    sino_da_dp_8=2600000
    sino_imp_lc_3=400000
    sino_da_dp_3=400000
    line_0=0

    banking_line_summary= {
        "ctbc_imp_lc_8":ctbc_imp_lc_8,
        "ctbc_imp_lc_3":ctbc_imp_lc_3,
        "cub_lc_da_dp" : cub_lc_da_dp,
        "scsb_imp_lc_da_dp_8" : cub_lc_da_dp,
        "scsb_imp_lc_da_dp_3" : cub_lc_da_dp,
        "sino_cln" : sino_cln,
        "sino_imp_lc_8" :sino_imp_lc_8,
        "sino_da_dp_8" : sino_da_dp_8,
        "sino_imp_lc_3": sino_imp_lc_3,
        "sino_da_dp_3" : sino_da_dp_3

        }

    banking_line= {
        "CTBC": {
            "GDI": {
                "Cash Loan": line_0,"Import Loan": ctbc_imp_lc_8,"LC Open": ctbc_imp_lc_8,"DA": line_0,"DP": line_0
                },
            "Tunwa Inds.": {
                "Cash Loan": line_0, "Import Loan": ctbc_imp_lc_3,"LC Open": ctbc_imp_lc_3,"DA": line_0,"DP": line_0
                },
            "UXL- Taiwan": {
                "Cash Loan": line_0,"Import Loan": line_0,"LC Open": line_0,"DA": line_0,"DP": line_0
                }
            },
        "CUB": {
            "GDI": {
                "Cash Loan": line_0,"Import Loan": line_0,"LC Open": cub_lc_da_dp,"DA": cub_lc_da_dp,"DP": cub_lc_da_dp
            },
            "Tunwa Inds.": {
                "Cash Loan": line_0,"Import Loan": line_0,"LC Open": cub_lc_da_dp,"DA": cub_lc_da_dp,"DP": cub_lc_da_dp
            },
            "UXL- Taiwan": {
                "Cash Loan": line_0,"Import Loan": line_0,"LC Open": cub_lc_da_dp,"DA": cub_lc_da_dp,"DP": cub_lc_da_dp
            }
        },
        "SCSB": {
            "GDI": {
                "Cash Loan": line_0,"Import Loan": scsb_imp_lc_da_dp_8,"LC Open": scsb_imp_lc_da_dp_8, "DA": scsb_imp_lc_da_dp_8, "DP": scsb_imp_lc_da_dp_8
            },
            "Tunwa Inds.": {
                "Cash Loan": line_0,"Import Loan": scsb_imp_lc_da_dp_3,"LC Open": scsb_imp_lc_da_dp_3, "DA": scsb_imp_lc_da_dp_3, "DP": scsb_imp_lc_da_dp_3
            },
            "UXL- Taiwan": {
                "Cash Loan": line_0, "Import Loan": line_0, "LC Open": line_0, "DA": line_0, "DP": line_0
            }
        },
        "SINO": {
            "GDI": {
                "Cash Loan": sino_cln, "Import Loan": sino_imp_lc_8, "LC Open": sino_imp_lc_8, "DA": sino_da_dp_8, "DP": sino_da_dp_8
            },
            "Tunwa Inds.": {
                "Cash Loan": sino_cln, "Import Loan": sino_imp_lc_3, "LC Open": sino_imp_lc_3, "DA": sino_da_dp_3, "DP": sino_da_dp_3
            },
            "UXL- Taiwan": {
                "Cash Loan": sino_cln, "Import Loan": line_0, "LC Open": line_0, "DA": line_0, "DP": line_0
            }
        }
    }

    
    return banking_line
    # return banking_line_summary


@frappe.whitelist()
def export_banking_data(as_on):
    """
    Fetch CIF Sheet + related banking data.
    :param as_on: Date (string or datetime) - filter date
    :return: list of dicts
    """
    query = """
        SELECT
            cif.name,
            cif.inv_no,
            com.company_code AS com,
            bank.bank,
            cif.payment_term AS p_term,
            ROUND(cif.document, 0) * 1.0 AS document,
            GREATEST(
                IFNULL(nego.total_nego, 0) - IFNULL(ref.total_ref, 0) - IFNULL(rec.total_rec, 0),
                0
            ) * 1.0 AS nego
        FROM `tabCIF Sheet` cif
        LEFT JOIN (
            SELECT inv_no, SUM(nego_amount) * 1.0 AS total_nego
            FROM `tabDoc Nego`
            WHERE nego_date <= %(as_on)s
            GROUP BY inv_no
        ) nego ON cif.name = nego.inv_no
        LEFT JOIN (
            SELECT inv_no, SUM(refund_amount) * 1.0 AS total_ref
            FROM `tabDoc Refund`
            WHERE refund_date <= %(as_on)s
            GROUP BY inv_no
        ) ref ON cif.name = ref.inv_no
        LEFT JOIN (
            SELECT inv_no, SUM(received) * 1.0 AS total_rec
            FROM `tabDoc Received`
            WHERE received_date <= %(as_on)s
            GROUP BY inv_no
        ) rec ON cif.name = rec.inv_no
        LEFT JOIN `tabBank` bank ON cif.bank = bank.name
        LEFT JOIN `tabCompany` com ON cif.shipping_company= com.name
        WHERE cif.payment_term != 'TT'
          AND GREATEST(
              IFNULL(nego.total_nego, 0) - IFNULL(ref.total_ref, 0) - IFNULL(rec.total_rec, 0),
              0
          ) != 0
          AND cif.inv_date <= %(as_on)s
        ORDER BY cif.name ASC
    """

    rows = frappe.db.sql(query, {"as_on": as_on}, as_dict=True)
    return [dict(row) for row in rows]

@frappe.whitelist()
def import_banking_data(as_on):
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
    return [dict(row) for row in rows]