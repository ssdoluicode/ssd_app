
import openpyxl
from openpyxl.styles import Font, Alignment
import frappe
from frappe.utils import today


def generate_daily_banking(as_on=today()):
    wb = openpyxl.Workbook()

    # -----------------------------
    # SHEET 1: Doc Received
    # -----------------------------
    data = frappe.db.sql("""
        SELECT 
            cif.inv_no AS inv_no, 
            dr.received_date AS date,
            cus.customer AS customer,
            bank.bank AS bank, 
            dr.received AS received 
        FROM `tabDoc Received` dr
        LEFT JOIN `tabCIF Sheet` cif ON cif.name = dr.inv_no
        LEFT JOIN `tabBank` bank ON bank.name = dr.bank
        LEFT JOIN `tabCustomer` cus ON cus.name = dr.customer
        WHERE DATE(dr.creation) = %s 
        OR DATE(dr.received_date) = %s
    """, (as_on, as_on), as_dict=True)

    ws1 = wb.active
    ws1.title = "Doc Received"
    headers = ["Inv No", "Rec Date", "Customer", "Bank", "Rec Amount"]
    ws1.append(headers)

    for c in ws1[1]:
        c.font = Font(bold=True)
        c.alignment = Alignment(horizontal="center")

    for row in data:
        ws1.append([
            row.inv_no or "",
            row.date or "",
            row.customer or "",
            row.bank or "",
            row.received or 0
        ])

    for c, w in {"A":18,"B":14,"C":25,"D":20,"E":16}.items():
        ws1.column_dimensions[c].width = w


    # -----------------------------
    # SHEET 2: Doc Negotiation
    # -----------------------------
    data2 = frappe.db.sql("""
        SELECT 
            cif.inv_no AS inv_no, 
            dn.nego_date AS date,
            cus.customer AS customer, 
            noti.notify AS notify, 
            bank.bank AS bank, 
            dn.nego_amount AS nego
        FROM `tabDoc Nego` dn
        LEFT JOIN `tabCIF Sheet` cif ON cif.name = dn.inv_no
        LEFT JOIN `tabBank` bank ON bank.name = dn.bank
        LEFT JOIN `tabCustomer` cus ON cus.name = dn.customer
        LEFT JOIN `tabNotify` noti ON noti.name = dn.notify
        WHERE DATE(dn.creation) = %s 
        OR DATE(dn.nego_date) = %s
    """, (as_on, as_on), as_dict=True)

    ws2 = wb.create_sheet("Doc Negotiation")
    headers2 = ["Inv No", "Nego Date", "Customer", "Notify", "Bank", "Nego Amount"]
    ws2.append(headers2)

    for c in ws2[1]:
        c.font = Font(bold=True)
        c.alignment = Alignment(horizontal="center")

    for row in data2:
        ws2.append([
            row.inv_no or "",
            row.date or "",
            row.customer or "",
            row.notify or "",
            row.bank or "",
            row.nego or 0
        ])

    for c, w in {"A":18,"B":14,"C":25,"D":20,"E":18,"F":18}.items():
        ws2.column_dimensions[c].width = w


    # -----------------------------
    # SHEET 3: Doc Refund
    # -----------------------------
    data3 = frappe.db.sql("""
        SELECT 
            cif.inv_no AS inv_no, 
            dr.refund_date AS date,
            cus.customer AS customer, 
            noti.notify AS notify, 
            bank.bank AS bank, 
            dr.refund_amount AS refund
        FROM `tabDoc Refund` dr
        LEFT JOIN `tabCIF Sheet` cif ON cif.name = dr.inv_no
        LEFT JOIN `tabBank` bank ON bank.name = dr.bank
        LEFT JOIN `tabCustomer` cus ON cus.name = dr.customer
        LEFT JOIN `tabNotify` noti ON noti.name = dr.notify
        WHERE DATE(dr.creation) = %s 
        OR DATE(dr.refund_date) = %s
    """, (as_on, as_on), as_dict=True)

    ws3 = wb.create_sheet("Doc Refund")
    headers3 = ["Inv No", "Refund Date", "Customer", "Notify", "Bank", "Refund Amount"]
    ws3.append(headers3)

    for c in ws3[1]:
        c.font = Font(bold=True)
        c.alignment = Alignment(horizontal="center")

    for row in data3:
        ws3.append([
            row.inv_no or "",
            row.date or "",
            row.customer or "",
            row.notify or "",
            row.bank or "",
            row.refund or 0
        ])

    for c, w in {"A":18,"B":14,"C":25,"D":20,"E":18,"F":18}.items():
        ws3.column_dimensions[c].width = w


    # -----------------------------
    # SHEET 4: CC Received  (Corrected)
    # -----------------------------
    data4 = frappe.db.sql("""
        SELECT 
            ccr.date AS date,
            cus.customer AS customer, 
            ccr.amount_usd AS cc_received
        FROM `tabCC Received` ccr
        LEFT JOIN `tabCustomer` cus ON cus.name = ccr.customer
        WHERE DATE(ccr.creation) = %s 
        OR DATE(ccr.date) = %s
    """, (as_on, as_on), as_dict=True)

    ws4 = wb.create_sheet("CC Received")
    headers4 = ["Date", "Customer", "CC Amount"]
    ws4.append(headers4)

    for c in ws4[1]:
        c.font = Font(bold=True)
        c.alignment = Alignment(horizontal="center")

    for row in data4:
        ws4.append([
            row.date or "",
            row.customer or "",
            row.cc_received or 0
        ])

    for c, w in {"A":18,"B":25,"C":18}.items():
        ws4.column_dimensions[c].width = w

    # -----------------------------
    # SHEET 5: Bank liability
    # -----------------------------

    data5 = frappe.db.sql("""
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

    """, {"as_on": as_on}, as_dict=True)

    ws5 = wb.create_sheet("Bank Liability")
    headers5 = [ "Inv No", "Date", "Bank", "Term", "Com", "Nego Amount"]
    ws5.append(headers5)

    for c in ws5[1]:
        c.font = Font(bold=True)
        c.alignment = Alignment(horizontal="center")

    for row in data5:
        ws5.append([
            row.inv_no or "",
            row.date or "",
            row.bank or "",
            row.p_term or "",
            row.com or "",
            row.nego or 0,
        ])


    # -----------------------------
    # SHEET 6: Bank Liability Pivot
    # -----------------------------

    # Step 1: Build pivot structure
    pivot = {}
    p_terms = sorted({row.p_term for row in data5})

    for row in data5:
        bank = row.bank
        com = row.com
        term = row.p_term
        nego = row.nego or 0

        pivot.setdefault(bank, {})
        pivot[bank].setdefault(com, {})
        pivot[bank][com][term] = pivot[bank][com].get(term, 0) + nego

    # Step 2: Create sheet
    ws6 = wb.create_sheet("Bank Liability Pivot")

    # Header row
    headers6 = ["Bank", "Com"] + p_terms + ["Total"]
    ws6.append(headers6)

    for c in ws6[1]:
        c.font = Font(bold=True)
        c.alignment = Alignment(horizontal="center")

    # Step 3: Add pivot rows
    grand_totals = {pt: 0 for pt in p_terms}
    grand_totals["Total"] = 0

    for bank, com_data in pivot.items():
        for com, term_data in com_data.items():
            row = [bank, com]

            total = 0
            for pt in p_terms:
                val = term_data.get(pt, 0)
                row.append(val)
                total += val
                grand_totals[pt] += val

            row.append(total)
            grand_totals["Total"] += total

            ws6.append(row)

    # Step 4: Add GRAND TOTAL row
    grand_row = ["", "Grand Total"]

    for pt in p_terms:
        grand_row.append(grand_totals[pt])

    grand_row.append(grand_totals["Total"])

    ws6.append(grand_row)

    # Styling the GRAND TOTAL row
    last_row = ws6.max_row
    for cell in ws6[last_row]:
        cell.font = Font(bold=True)
        if isinstance(cell.value, (int, float)):
            cell.number_format = "#,##0.00"

    # Step 5: Number formatting for all number cells
    for row in ws6.iter_rows(min_row=2, min_col=3):  # from column C onwards
        for cell in row:
            if isinstance(cell.value, (int, float)):
                cell.number_format = "#,##0.00"

    # Step 6: Auto column width
    for col in ws6.columns:
        max_len = 0
        column = col[0].column_letter
        for cell in col:
            try:
                max_len = max(max_len, len(str(cell.value)))
            except:
                pass
        ws6.column_dimensions[column].width = max_len + 2
    # -----------------------------
    # Save workbook
    # -----------------------------
    file_path = frappe.utils.get_site_path("private", "files", "daily_banking.xlsx")
    wb.save(file_path)
    return file_path


def send_daily_banking_email():
    file_path = generate_daily_banking()

    with open(file_path, "rb") as f:
        file_data = f.read()

    frappe.sendmail(
        recipients=["ssdolui.in@gmail.com"],
        subject="Auto Excel Report",
        message="Please find the attached Excel report.",
        attachments=[{
            "fname": "daily_banking.xlsx",
            "fcontent": file_data,
            "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }]
    )

    return "Email sent."
