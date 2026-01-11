import frappe
from datetime import date
from frappe.utils import today



@frappe.whitelist()
def banking_line_data(as_on=today()):
   
    """
    Fetch CIF Sheet + related banking data.
    param as_on: Date (string or datetime) - filter date
    return: list of dicts
    """
    query = """
        WITH
        /* ---------------------------------------------------
        1. EXPORT BANKING (Safe Outstanding)
        --------------------------------------------------- */
        ExportBanking AS (
            SELECT
                cif.bank,
                cif.shipping_company AS com,
                cif.payment_term AS p_term,
                SUM(
                    GREATEST(
                        IFNULL(nego.amt, 0)
                    - IFNULL(ref.amt, 0)
                    - IFNULL(rec.amt, 0),
                    0)
                ) AS used_line
            FROM `tabCIF Sheet` cif

            LEFT JOIN (
                SELECT inv_no, SUM(nego_amount) AS amt
                FROM `tabDoc Nego`
                WHERE nego_date <= %(as_on)s
                GROUP BY inv_no
            ) nego ON nego.inv_no = cif.name

            LEFT JOIN (
                SELECT inv_no, SUM(refund_amount) AS amt
                FROM `tabDoc Refund`
                WHERE refund_date <= %(as_on)s
                GROUP BY inv_no
            ) ref ON ref.inv_no = cif.name

            LEFT JOIN (
                SELECT inv_no, SUM(received) AS amt
                FROM `tabDoc Received`
                WHERE received_date <= %(as_on)s
                GROUP BY inv_no
            ) rec ON rec.inv_no = cif.name

            WHERE cif.inv_date <= %(as_on)s
            AND cif.payment_term <> 'TT'

            GROUP BY cif.bank, cif.shipping_company, cif.payment_term
            HAVING used_line <> 0
        ),

        /* ---------------------------------------------------
        2. IMPORT BANKING (All Sources)
        --------------------------------------------------- */
        ImportBanking AS (

            /* ---------- LC OPEN ---------- */
            SELECT
                MAX(lc_o.bank) AS bank,
                MAX(lc_o.company) AS com,
                'LC Open' AS p_term,
                GREATEST(
                    SUM(lc_o.amount_usd)
                - IFNULL(lc_p.paid, 0)
                - IFNULL(imp_ln.moved, 0)
                - IFNULL(us_lc.moved, 0),
                0) AS used_line
            FROM `tabLC Open` lc_o

            LEFT JOIN (
                SELECT group_id, SUM(amount_usd) AS paid
                FROM `tabLC Payment`
                WHERE date <= %(as_on)s
                GROUP BY group_id
            ) lc_p ON lc_p.group_id = lc_o.group_id

            LEFT JOIN (
                SELECT group_id, SUM(loan_amount_usd) AS moved
                FROM `tabImport Loan`
                WHERE from_lc_open = 1
                AND loan_date <= %(as_on)s
                GROUP BY group_id
            ) imp_ln ON imp_ln.group_id = lc_o.group_id

            LEFT JOIN (
                SELECT group_id, SUM(usance_lc_amount_usd) AS moved
                FROM `tabUsance LC`
                WHERE from_lc_open = 1
                AND usance_lc_date <= %(as_on)s
                GROUP BY group_id
            ) us_lc ON us_lc.group_id = lc_o.group_id

            WHERE lc_o.lc_open_date <= %(as_on)s
            GROUP BY lc_o.group_id

            UNION ALL

            /* ---------- IMPORT LOAN ---------- */
            SELECT
                imp_l.bank,
                imp_l.company,
                'Imp Loan' AS p_term,
                ROUND(
                    GREATEST(
                        SUM(imp_l.loan_amount)
                    - IFNULL(SUM(p.paid), 0),
                    0) / NULLIF(AVG(imp_l.ex_rate), 0),
                2) AS used_line
            FROM `tabImport Loan` imp_l

            LEFT JOIN (
                SELECT inv_no, SUM(amount) AS paid
                FROM `tabImport Loan Payment`
                WHERE payment_date <= %(as_on)s
                GROUP BY inv_no
            ) p ON p.inv_no = imp_l.name

            WHERE imp_l.loan_date <= %(as_on)s
            GROUP BY imp_l.bank, imp_l.company

            UNION ALL

            /* ---------- USANCE LC ---------- */
            SELECT
                u.bank,
                u.company,
                'Usance LC' AS p_term,
                ROUND(
                    GREATEST(
                        u.usance_lc_amount - IFNULL(p.paid, 0),
                    0) / NULLIF(u.ex_rate, 0),
                2) AS used_line
            FROM `tabUsance LC` u

            LEFT JOIN (
                SELECT inv_no, SUM(amount) AS paid
                FROM `tabUsance LC Payment`
                WHERE payment_date <= %(as_on)s
                GROUP BY inv_no
            ) p ON p.inv_no = u.name

            WHERE u.usance_lc_date <= %(as_on)s
            GROUP BY u.bank, u.company

            UNION ALL

            /* ---------- CASH LOAN ---------- */
            SELECT
                c.bank,
                c.company,
                'Cash Loan' AS p_term,
                ROUND(
                    GREATEST(
                        c.cash_loan_amount - IFNULL(p.paid, 0),
                    0) / NULLIF(c.ex_rate, 0),
                2) AS used_line
            FROM `tabCash Loan` c

            LEFT JOIN (
                SELECT cash_loan_no, SUM(amount) AS paid
                FROM `tabCash Loan Payment`
                WHERE payment_date <= %(as_on)s
                GROUP BY cash_loan_no
            ) p ON p.cash_loan_no = c.name

            WHERE c.cash_loan_date <= %(as_on)s
            GROUP BY c.bank, c.company
        ),

        /* ---------------------------------------------------
        3. COMBINED BANKING
        --------------------------------------------------- */
        CombindBanking AS (
            SELECT * FROM ExportBanking
            UNION ALL
            SELECT * FROM ImportBanking
        ),

        /* ---------------------------------------------------
        4. LATEST BANKING LINE MAPPING
        --------------------------------------------------- */
        BankingLineMap AS (
            SELECT
                cbl.bank,
                cbl.company,
                cblb.payment_term,
                cblb.banking_line AS i_banking_line,
                cblb.combind_banking_line AS banking_line_name,
                ROW_NUMBER() OVER (
                    PARTITION BY cbl.bank_com_id, cblb.payment_term
                    ORDER BY cbl.date DESC, cbl.creation DESC
                ) AS rn
            FROM `tabCom Banking Line` cbl
            JOIN `tabCom Banking Line Breakup` cblb
                ON cblb.parent = cbl.name
            WHERE cbl.date <= %(as_on)s
        )

        /* ---------------------------------------------------
        5. FINAL SAFE OUTPUT
        --------------------------------------------------- */
        SELECT
            m.bank,
            m.company,
            m.payment_term,
            m.i_banking_line,
            IFNULL(b.used_line, 0) AS used_line,
            m.banking_line_name
        FROM BankingLineMap m
        LEFT JOIN CombindBanking b
            ON b.bank   = m.bank
            AND b.com    = m.company
            AND b.p_term = m.payment_term
        WHERE m.rn = 1
        ORDER BY m.bank, m.company, m.payment_term;

   
    """
    rows = frappe.db.sql(query, {"as_on": as_on}, as_dict=True)
    return [dict(row) for row in rows]



@frappe.whitelist()
def check_banking_line(bank, com, p_term, as_on=today()):
    banking_data = banking_line_data(as_on=as_on)

    # ---- Find target row ----
    data = next(
        (
            row.copy()
            for row in banking_data
            if row.get("bank") == bank
            and row.get("company") == com
            and row.get("payment_term") == p_term
        ),
        {}
    )

    # ---- Safety check ----
    if not data:
        return {
            "bank": bank,
            "company": com,
            "payment_term": p_term,
            "banking_line_name": None,
            "used_banking_line": 0,
            "no_limit": None,
            "banking_line": None
        }

    banking_line_name = data.get("banking_line_name")

    # ---- Sum used banking line ----
    used_banking_line = sum(
        row.get("used_line", 0)
        for row in banking_data
        if row.get("banking_line_name") == banking_line_name
    )

    data["used_banking_line"] = used_banking_line

    # ---- Fetch banking line info ----
    banking_line = frappe.db.get_value(
        "Bank Banking Line",
        {"name": banking_line_name},
        ["no_limit", "banking_line"],
        as_dict=True
    ) or {"no_limit": None, "banking_line": None}

    data.update(banking_line)
    print(data)

    return data





















