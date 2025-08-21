import frappe

@frappe.whitelist()
def banking_line_data():

    banking_line_summary= {
        "ctbc_imp_lc_8":2000000,
        "ctbc_imp_lc_3":1000000,
        "cub_lc_da_dp" : 8000000,
        "scsb_imp_lc_da_dp_8" : 3000000,
        "scsb_imp_lc_da_dp_3" : 500000,
        "sino_cln" : 1050000,
        "sino_imp_lc_8" :1100000,
        "sino_da_dp_8" : 2600000,
        "sino_imp_lc_3": 400000,
        "sino_da_dp_3" : 400000,
        "line_0" :0
        }

    return banking_line_summary


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


@frappe.whitelist()
def balance_banking_line_data(as_on):
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


    export_banking=export_banking_data(as_on)
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

    import_banking=import_banking_data(as_on)
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

    balance_line={
        "b_ctbc_imp_lc_8" : ctbc_imp_lc_8 - u_ctbc_imp_lc_8,
        "b_ctbc_imp_lc_3" : ctbc_imp_lc_3 - u_ctbc_imp_lc_3,
        "b_cub_lc_da_dp" : cub_lc_da_dp - u_cub_lc_da_dp,
        "b_scsb_imp_lc_da_dp_8" : scsb_imp_lc_da_dp_8 - u_scsb_imp_lc_da_dp_8,
        "b_scsb_imp_lc_da_dp_3" : scsb_imp_lc_da_dp_3 - u_scsb_imp_lc_da_dp_3,
        "b_sino_cln" : sino_cln - u_sino_cln,
        "b_sino_imp_lc_8" : sino_imp_lc_8 - u_sino_imp_lc_8,
        "b_sino_da_dp_8" : sino_da_dp_8 - u_sino_da_dp_8,
        "b_sino_imp_lc_3" : sino_imp_lc_3 - u_sino_imp_lc_3,
        "b_sino_da_dp_3" : sino_da_dp_3 - u_sino_da_dp_3
    }
    return balance_line
