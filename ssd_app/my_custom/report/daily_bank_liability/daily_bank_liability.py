
import frappe
from frappe.utils import today


def execute(filters=None):

    columns = [
        {"label": "Inv/LC No", "fieldname": "inv_no", "fieldtype": "Data", "width": 150},
        {"label": "Date", "fieldname": "date", "fieldtype": "Data", "width": 110},
        {"label": "Com", "fieldname": "com", "fieldtype": "Data", "width": 130},
        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 60},
        {"label": "P Term", "fieldname": "p_term", "fieldtype": "Data", "width": 90},
        {"label": "Amount", "fieldname": "nego", "fieldtype": "Float", "width": 100},
    ]

    data = frappe.db.sql("""
        SELECT
            cif.name AS name,
            cif.inv_no,
            cif.inv_date AS date,
            bank.bank,
            cif.payment_term AS p_term,
            com.company_code AS com,
            GREATEST(
                IFNULL(nego.total_nego, 0)
                - IFNULL(ref.total_ref, 0)
                - IFNULL(rec.total_rec, 0),
            0) AS nego
        FROM `tabCIF Sheet` cif
        LEFT JOIN (
            SELECT inv_no, SUM(nego_amount) AS total_nego
            FROM `tabDoc Nego`
            WHERE nego_date <= %(as_on)s
            GROUP BY inv_no
        ) nego ON cif.name = nego.inv_no
        LEFT JOIN (
            SELECT inv_no, SUM(refund_amount) AS total_ref
            FROM `tabDoc Refund`
            WHERE refund_date <= %(as_on)s
            GROUP BY inv_no
        ) ref ON cif.name = ref.inv_no
        LEFT JOIN (
            SELECT inv_no, SUM(received) AS total_rec
            FROM `tabDoc Received`
            WHERE received_date <= %(as_on)s
            GROUP BY inv_no
        ) rec ON cif.name = rec.inv_no
        LEFT JOIN `tabBank` bank ON cif.bank = bank.name
        LEFT JOIN `tabCompany` com ON com.name = cif.shipping_company
        WHERE cif.inv_date <= %(as_on)s
        AND GREATEST(
                IFNULL(nego.total_nego, 0)
                - IFNULL(ref.total_ref, 0)
                - IFNULL(rec.total_rec, 0),
            0) > 0

        UNION ALL

        SELECT
            NULL AS name,
            NULL AS inv_no,
            NULL AS date,
            bank.bank AS bank,
            'LC Open' AS p_term,
            com.company_code AS com,
            IFNULL(o.lcp_amount, 0) - IFNULL(p.lcp_amount, 0) AS nego
        FROM (
            SELECT bank, company, SUM(amount) AS lcp_amount
            FROM `tabLC Open`
            WHERE lc_open_date <= %(as_on)s
            GROUP BY bank, company
        ) o
        LEFT JOIN (
            SELECT bank, company, SUM(amount) AS lcp_amount
            FROM `tabLC Payment`
            WHERE date <= %(as_on)s
            GROUP BY bank, company
        ) p ON o.bank = p.bank AND o.company = p.company
        LEFT JOIN `tabBank` bank ON COALESCE(o.bank, p.bank) = bank.name
        LEFT JOIN `tabCompany` com ON COALESCE(o.company, p.company) = com.name
        WHERE IFNULL(o.lcp_amount, 0) - IFNULL(p.lcp_amount, 0) > 0

        UNION ALL

        SELECT 
            iloan.name,
            iloan.inv_no,
            iloan.loan_date AS date,
            bank.bank,
            'Imp Loan' AS p_term,
            com.company_code AS com,
            GREATEST(
                (COALESCE(iloan.loan_amount, 0) - COALESCE(iloanp.iloanp_amount, 0))
                    / COALESCE(lco.ex_rate, 1),
            0) AS nego
        FROM `tabImport Loan` iloan
        LEFT JOIN `tabLC Open` lco ON lco.name = iloan.lc_no
        LEFT JOIN `tabBank` bank ON bank.name = iloan.bank
        LEFT JOIN `tabCompany` com ON com.name = iloan.company
        LEFT JOIN (
            SELECT inv_no, SUM(amount) AS iloanp_amount
            FROM `tabImport Loan Payment`
            WHERE payment_date <= %(as_on)s
            GROUP BY inv_no
        ) iloanp ON iloanp.inv_no = iloan.name
        WHERE iloan.loan_date <= %(as_on)s
        AND GREATEST(
                (COALESCE(iloan.loan_amount, 0) - COALESCE(iloanp.iloanp_amount, 0))
                    / COALESCE(lco.ex_rate, 1),
            0) > 0

        UNION ALL

        SELECT 
            ulc.name,
            ulc.inv_no,
            ulc.usance_lc_date AS date,
            bank.bank,
            'Usance LC' AS p_term,
            com.company_code AS com,
            GREATEST(
                COALESCE(ulc.usance_lc_amount, 0) / COALESCE(ulc.ex_rate, 1)
                - COALESCE(ulcp.ulcp_amount, 0) / COALESCE(ulc.ex_rate, 1),
            0) AS nego
        FROM `tabUsance LC` ulc
        LEFT JOIN `tabCompany` com ON com.name = ulc.company
        LEFT JOIN `tabBank` bank ON bank.name = ulc.bank
        LEFT JOIN (
            SELECT inv_no, SUM(amount) AS ulcp_amount
            FROM `tabUsance LC Payment`
            WHERE payment_date <= %(as_on)s
            GROUP BY inv_no
        ) ulcp ON ulcp.inv_no = ulc.name
        WHERE ulc.usance_lc_date <= %(as_on)s
        AND GREATEST(
                COALESCE(ulc.usance_lc_amount, 0) / COALESCE(ulc.ex_rate, 1)
                - COALESCE(ulcp.ulcp_amount, 0) / COALESCE(ulc.ex_rate, 1),
            0) > 0

        UNION ALL

        SELECT 
            cln.name,
            cln.cash_loan_no AS inv_no,
            cln.cash_loan_date AS date,
            bank.bank,
            'Cash Loan' AS p_term,
            com.company_code AS com,
            GREATEST(
                COALESCE(cln.cash_loan_amount / cln.ex_rate, 0)
                - COALESCE(clnp.clnp_amount / cln.ex_rate, 0),
            0) AS nego
        FROM `tabCash Loan` cln
        LEFT JOIN `tabCompany` com ON com.name = cln.company
        LEFT JOIN `tabBank` bank ON bank.name = cln.bank
        LEFT JOIN (
            SELECT cash_loan_no, SUM(amount) AS clnp_amount
            FROM `tabCash Loan Payment`
            WHERE payment_date <= %(as_on)s
            GROUP BY cash_loan_no
        ) clnp ON clnp.cash_loan_no = cln.name
        WHERE cln.cash_loan_date <= %(as_on)s
        AND GREATEST(
                COALESCE(cln.cash_loan_amount / cln.ex_rate, 0)
                - COALESCE(clnp.clnp_amount / cln.ex_rate, 0),
            0) > 0

    """, {"as_on": today()}, as_dict=True)

    # Format date
    for row in data:
        if row.get("date") and hasattr(row["date"], "strftime"):
            row["date"] = row["date"].strftime("%d-%b-%y")

    return columns, data
