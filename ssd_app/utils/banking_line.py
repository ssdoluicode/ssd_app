import frappe
from datetime import date
from frappe.utils import today


# ⚠️ DEVELOPER_NOTE
# ------------------------------------------------------------
# Before updating, editing, or refactoring this,
# PLEASE read:
# ssd_app/utils/Banking_Line_Architecture_Note.txt
# ------------------------------------------------------------


@frappe.whitelist()
def banking_line_data(as_on=today()):
   
    """
    Fetch CIF Sheet + related banking data.
    param as_on: Date (string or datetime) - filter date
    return: list of dicts
    """
    query= """
            WITH
        /* ---------------------------------------------------
        1. EXPORT BANKING (Safe Outstanding)
        --------------------------------------------------- */
        ExportBanking AS (
            SELECT
                shi.bank,
                shi.company AS com,
                shi.payment_term AS p_term,
                SUM(
                    GREATEST(
                        IFNULL(nego.amt, 0)
                    - IFNULL(ref.amt, 0)
                    - IFNULL(rec.amt, 0),
                        0
                    )
                ) AS used_line
            FROM `tabShipping Book` shi

            LEFT JOIN (
                SELECT inv_no, SUM(nego_amount) AS amt
                FROM `tabDoc Nego`
                WHERE nego_date <= %(as_on)s
                GROUP BY inv_no
            ) nego ON nego.inv_no = shi.name

            LEFT JOIN (
                SELECT inv_no, SUM(refund_amount) AS amt
                FROM `tabDoc Refund`
                WHERE refund_date <= %(as_on)s
                GROUP BY inv_no
            ) ref ON ref.inv_no = shi.name

            LEFT JOIN (
                SELECT inv_no, SUM(received) AS amt
                FROM `tabDoc Received`
                WHERE received_date <= %(as_on)s
                GROUP BY inv_no
            ) rec ON rec.inv_no = shi.name

            WHERE shi.bl_date <= %(as_on)s
            AND shi.payment_term <> 'TT'

            GROUP BY shi.bank, shi.company, shi.payment_term
            HAVING used_line <> 0
        ),

        /* ---------------------------------------------------
        2. IMPORT BANKING
        --------------------------------------------------- */
        ImportBanking AS (

            /* ---------- LC OPEN ---------- */
            SELECT
                MAX(lc_o.bank) AS bank,
                MAX(lc_o.company) AS com,
                pt.name AS p_term,
                GREATEST(
                    SUM(lc_o.amount_usd)
                - IFNULL(lc_p.paid, 0)
                - IFNULL(imp_ln.moved, 0)
                - IFNULL(us_lc.moved, 0),
                    0
                ) AS used_line
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
            LEFT JOIN `tabPayment Term` pt ON pt.term_name= "LC Open"

            WHERE lc_o.lc_open_date <= %(as_on)s
            GROUP BY lc_o.group_id

            UNION ALL

            /* ---------- IMPORT LOAN ---------- */
            SELECT
                imp_l.bank,
                imp_l.company,
                pt.name AS p_term,
                ROUND(
                    GREATEST(
                        SUM(imp_l.loan_amount) - IFNULL(SUM(p.paid), 0),
                        0
                    ) / NULLIF(AVG(imp_l.ex_rate), 0),
                    2
                ) AS used_line
            FROM `tabImport Loan` imp_l

            LEFT JOIN (
                SELECT inv_no, SUM(amount) AS paid
                FROM `tabImport Loan Payment`
                WHERE payment_date <= %(as_on)s
                GROUP BY inv_no
            ) p ON p.inv_no = imp_l.name
            LEFT JOIN `tabPayment Term` pt ON pt.term_name= "Import Loan"

            WHERE imp_l.loan_date <= %(as_on)s
            GROUP BY imp_l.bank, imp_l.company
            
            UNION ALL

            /* ---------- USANCE LC ---------- */
            SELECT
                u.bank,
                u.company,
                -- We use MAX or MIN for p_term because it is a constant string "Usance LC"
                MAX(pt.name) AS p_term, 
                -- Wrap the entire calculation in a SUM to get the total per Bank/Company
                SUM(
                    ROUND(
                        GREATEST(
                            u.usance_lc_amount - IFNULL(p.paid, 0),
                            0
                        ) / NULLIF(u.ex_rate, 0),
                        2
                    )
                ) AS used_line
            FROM `tabUsance LC` u
            LEFT JOIN (
                SELECT inv_no, SUM(amount) AS paid
                FROM `tabUsance LC Payment`
                WHERE payment_date <= %(as_on)s
                GROUP BY inv_no
            ) p ON p.inv_no = u.name
            LEFT JOIN `tabPayment Term` pt ON pt.term_name = "Usance LC"

            WHERE u.usance_lc_date <= %(as_on)s
            GROUP BY u.bank, u.company

            UNION ALL

            /* ---------- CASH LOAN ---------- */
            
            SELECT
                c.bank,
                c.company,
                pt.name AS p_term,
                ROUND(
                    GREATEST(
                        c.cash_loan_amount - IFNULL(p.paid, 0),
                        0
                    ) / NULLIF(c.ex_rate, 0),
                    2
                ) AS used_line
            FROM `tabCash Loan` c
            LEFT JOIN (
                SELECT cash_loan_no, SUM(amount) AS paid
                FROM `tabCash Loan Payment`
                WHERE payment_date <= %(as_on)s 
                GROUP BY cash_loan_no
            ) p ON p.cash_loan_no = c.name
            LEFT JOIN `tabPayment Term` pt ON pt.term_name = "Cash Loan"
            WHERE c.cash_loan_date <= %(as_on)s
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
        5. FINAL OUTPUT
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
            "sub_limit": 0,
            "total_used_line": 0,
            "banking_line_name": None,
            "no_limit": None,
            "banking_line": None,
            "balance_line": 0
        }

    banking_line_name = data.get("banking_line_name")
    total_used_line=0
    for i in banking_data:
        if i["banking_line_name"] == banking_line_name:
            total_used_line+=i["used_line"]

    # ---- Fetch banking line info ----
    banking_line = frappe.db.get_value(
        "Bank Banking Line",
        {"name": banking_line_name},
        ["no_limit", "banking_line"],
        as_dict=True
    ) or {"no_limit": None, "banking_line": None}



    total_used_sub_limit=0
    sub_limit_name = data.get("i_banking_line")
    if(data.get("i_banking_line")):
        for i in banking_data:
            if i["i_banking_line"] == sub_limit_name:
                total_used_sub_limit+=i["used_line"]
    
    # ---- Fetch banking line info ----
    sub_limit = frappe.db.get_value("Banking Line Sub Limit",sub_limit_name,"sub_limit_amount") or 0

    # ---- Keep only required fields ----
    result = {
        "sub_limit": sub_limit-total_used_sub_limit,
        "total_used_line": total_used_line,
        "banking_line_name": banking_line_name,
        "no_limit": banking_line.get("no_limit"),
        "banking_line": banking_line.get("banking_line")
    }

    # ---- Compute balance_line ----
    if result["no_limit"] == 1:
        result["balance_line"] = -1
    elif result["sub_limit"] > 0:
        result["balance_line"] = result["sub_limit"]
    else:
        result["balance_line"] = (result["banking_line"] or 0) - total_used_line
    print(result)
    return result



@frappe.whitelist()
def banking_lines_position(as_on=today()):
    banking_data = banking_line_data(as_on=as_on)
    # Initialize an empty dictionary to store totals
    line_totals = {}

    for entry in banking_data:
        line_name = entry.get('banking_line_name')
        used_amount = entry.get('used_line', 0.0)
        
        # Add the used_line amount to the existing total for this banking_line_name
        if line_name in line_totals:
            line_totals[line_name] += used_amount
        else:
            line_totals[line_name] = used_amount

    # Print the results
    position={}
    for line, total in line_totals.items():
        line_amount= frappe.db.get_value("Bank Banking Line", line, ["no_limit", "banking_line"], as_dict=True)
        if not line_amount:
            continue

        no_limit = line_amount.no_limit or 0
        limit= line_amount.banking_line or 0
        used = total or 0
        if no_limit==1:
            balance=-1
        else:
            balance = limit - used

        position[line] = {
            "used": round(used,2),
            "balance": round(balance,2)
        }
    return position
















