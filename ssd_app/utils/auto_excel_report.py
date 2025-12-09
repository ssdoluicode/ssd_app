# import openpyxl
# from openpyxl.styles import Font, Alignment
# import frappe
# import os
# from frappe.utils import today

# import openpyxl
# from openpyxl.styles import Font, Alignment
# import frappe
# from frappe.utils import today

# def generate_daily_banking(as_on=today()):
#     # Create workbook
#     wb = openpyxl.Workbook()

#     # -----------------------------
#     # SHEET 1: Doc Received
#     # -----------------------------
#     data = frappe.db.sql("""
#         SELECT 
#             cif.inv_no AS inv_no, 
#             dr.received_date AS date,
#             cus.customer AS customer, 
#             bank.bank AS bank, 
#             dr.received AS received 
#         FROM `tabDoc Received` dr
#         LEFT JOIN `tabCIF Sheet` cif ON cif.name = dr.inv_no
#         LEFT JOIN `tabBank` bank ON bank.name = dr.bank
#         LEFT JOIN `tabCustomer` cus ON cus.name = dr.customer
#         WHERE DATE(dr.creation) = %s 
#         OR DATE(dr.received_date) = %s
#     """, (as_on, as_on), as_dict=True)

#     ws1 = wb.active
#     ws1.title = "Doc Received"

#     headers = ["Inv No", "Rec Date", "Customer", "Bank", "Rec Amount"]
#     ws1.append(headers)

#     # Style headers
#     for cell in ws1[1]:
#         cell.font = Font(bold=True)
#         cell.alignment = Alignment(horizontal="center")

#     # Write rows
#     for row in data:
#         ws1.append([
#             row.inv_no or "",
#             row.date or "",
#             row.customer or "",
#             row.bank or "",
#             row.received or 0
#         ])

#     # Column widths
#     width_map_1 = {"A": 18, "B": 14, "C": 25, "D": 20, "E": 16}
#     for col, width in width_map_1.items():
#         ws1.column_dimensions[col].width = width

#     # -----------------------------
#     # SHEET 2: Doc Negotiation
#     # -----------------------------
#     data2 = frappe.db.sql("""
#         SELECT 
#             cif.inv_no AS inv_no, 
#             dn.nego_date AS date,
#             cus.customer AS customer, 
#             noti.notify AS notify, 
#             bank.bank AS bank, 
#             dn.nego_amount AS nego
#         FROM `tabDoc Nego` dn
#         LEFT JOIN `tabCIF Sheet` cif ON cif.name = dn.inv_no
#         LEFT JOIN `tabBank` bank ON bank.name = dn.bank
#         LEFT JOIN `tabCustomer` cus ON cus.name = dn.customer
#         LEFT JOIN `tabNotify` noti ON noti.name = dn.notify
#         WHERE DATE(dn.creation) = %s 
#         OR DATE(dn.nego_date) = %s
#     """, (as_on, as_on), as_dict=True)

#     ws2 = wb.create_sheet("Doc Negotiation")

#     headers2 = ["Inv No", "Nego Date", "Customer", "Notify", "Bank", "Nego Amount"]
#     ws2.append(headers2)

#     # Style headers
#     for cell in ws2[1]:
#         cell.font = Font(bold=True)
#         cell.alignment = Alignment(horizontal="center")

#     # Write rows
#     for row in data2:
#         ws2.append([
#             row.inv_no or "",
#             row.date or "",
#             row.customer or "",
#             row.notify or "",
#             row.bank or "",
#             row.nego or 0
#         ])

#     # Column widths
#     width_map_2 = {"A": 18, "B": 14, "C": 25, "D": 20, "E": 18, "F": 18}
#     for col, width in width_map_2.items():
#         ws2.column_dimensions[col].width = width

    
#     # -----------------------------
#     # SHEET 3: Doc Refund
#     # -----------------------------
#     data3 = frappe.db.sql("""
#         SELECT 
#             cif.inv_no AS inv_no, 
#             dr.refund_date AS date,
#             cus.customer AS customer, 
#             noti.notify AS notify, 
#             bank.bank AS bank, 
#             dr.refund_amount AS refund
#         FROM `tabDoc Refund` dr
#         LEFT JOIN `tabCIF Sheet` cif ON cif.name = dr.inv_no
#         LEFT JOIN `tabBank` bank ON bank.name = dr.bank
#         LEFT JOIN `tabCustomer` cus ON cus.name = dr.customer
#         LEFT JOIN `tabNotify` noti ON noti.name = dr.notify
#         WHERE DATE(dr.creation) = %s 
#         OR DATE(dr.refund_date) = %s
#     """, (as_on, as_on), as_dict=True)

#     ws3 = wb.create_sheet("Doc Refund")

#     headers3 = ["Inv No", "Refund Date", "Customer", "Notify", "Bank", "Refund Amount"]
#     ws3.append(headers3)

#     # Style headers
#     for cell in ws3[1]:
#         cell.font = Font(bold=True)
#         cell.alignment = Alignment(horizontal="center")

#     # Write rows
#     for row in data3:
#         ws3.append([
#             row.inv_no or "",
#             row.date or "",
#             row.customer or "",
#             row.notify or "",
#             row.bank or "",
#             row.nego or 0
#         ])

#     # Column widths
#     width_map_3 = {"A": 18, "B": 14, "C": 25, "D": 20, "E": 18, "F": 18}
#     for col, width in width_map_3.items():
#         ws3.column_dimensions[col].width = width


#     # -----------------------------
#     # SHEET 4: Doc Refund
#     # -----------------------------
#     data4 = frappe.db.sql("""
#         SELECT 
#             ccr.date AS date,
#             cus.customer AS customer, 
#             ccr.amount_usd AS cc_received
#         FROM `tabCC Received` ccr
#         LEFT JOIN `tabCustomer` cus ON cus.name = ccr.customer
#         WHERE DATE(ccr.creation) = %s 
#         OR DATE(ccr.date) = %s
#     """, (as_on, as_on), as_dict=True)

#     ws4 = wb.create_sheet("CC Received")

#     headers4 = ["Date", "Customer","CC Amount"]
#     ws4.append(headers4)

#     # Style headers
#     for cell in ws4[1]:
#         cell.font = Font(bold=True)
#         cell.alignment = Alignment(horizontal="center")

#     # Write rows
#     for row in data4:
#         ws3.append([
#             row.inv_no or "",
#             row.date or "",
#             row.customer or "",
#             row.notify or "",
#             row.bank or "",
#             row.nego or 0
#         ])

#     # Column widths
#     width_map_4 = {"A": 18, "B": 14, "C": 25}
#     for col, width in width_map_4.items():
#         ws4.column_dimensions[col].width = width


#     # -----------------------------
#     # Save File
#     # -----------------------------
#     file_path = frappe.utils.get_site_path("private", "files", "daily_banking.xlsx")
#     wb.save(file_path)

#     return file_path



# def send_daily_banking_email():
#     file_path = generate_daily_banking()

#     # Read file bytes
#     with open(file_path, "rb") as f:
#         file_data = f.read()

#     # Send email
#     frappe.sendmail(
#         recipients=["sasdolui.in@gmail.com"],
#         subject="Auto Excel Report",
#         message="Please find the attached Excel report.",
#         attachments=[{
#             "fname": "auto_report.xlsx",
#             "fcontent": file_data,
#             "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#         }]
#     )

#     return "Email sent."


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
        recipients=["sasdolui.in@gmail.com"],
        subject="Auto Excel Report",
        message="Please find the attached Excel report.",
        attachments=[{
            "fname": "daily_banking.xlsx",
            "fcontent": file_data,
            "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }]
    )

    return "Email sent."
