import openpyxl
from openpyxl.styles import Font, Alignment
import frappe
import os
from frappe.utils import today

def generate_daily_banking(as_on=today()):
    # Create workbook
    wb = openpyxl.Workbook()

    # Sheet 1
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

    # Write header row
    headers = ["Inv No", "Date", "Customer", "Bank", "Received Amount"]
    ws1.append(headers)

    # Apply header style
    for cell in ws1[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    # Write data rows
    for row in data:
        ws1.append([
            row.inv_no or "",
            row.date or "",
            row.customer or "",
            row.bank or "",
            row.received or 0
        ])

    # Adjust column widths
    width_map = {
        "A": 18,
        "B": 14,
        "C": 25,
        "D": 20,
        "E": 16
    }
    for col, width in width_map.items():
        ws1.column_dimensions[col].width = width


    # Sheet 2
    ws2 = wb.create_sheet("Stock")
    ws2.append(["Item", "Qty"])
    ws2.append(["Pen", 10])
    ws2.append(["Book", 5])

    # Generate local file path
    file_path = frappe.utils.get_site_path("private", "files", "daily_banking.xlsx")

    # Save Excel locally
    wb.save(file_path)

    return file_path


def send_daily_banking_email():
    file_path = generate_daily_banking()

    # Read file bytes
    with open(file_path, "rb") as f:
        file_data = f.read()

    # Send email
    frappe.sendmail(
        recipients=["sasdolui.in@gmail.com"],
        subject="Auto Excel Report",
        message="Please find the attached Excel report.",
        attachments=[{
            "fname": "auto_report.xlsx",
            "fcontent": file_data,
            "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }]
    )

    return "Email sent."
