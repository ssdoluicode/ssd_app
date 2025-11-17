import openpyxl
import frappe
import os

def generate_daily_banking():
    # Create workbook
    wb = openpyxl.Workbook()

    # Sheet 1
    ws1 = wb.active
    ws1.title = "Sales"
    ws1.append(["Customer", "Amount"])
    ws1.append(["A", 150])
    ws1.append(["B", 300])

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
