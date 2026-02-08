# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.pdf import get_pdf
from frappe.utils import now_datetime
from frappe import _

@frappe.whitelist()
def get_cif_data(inv_no):
    cif = frappe.get_doc("CIF Sheet", inv_no)
    sb= frappe.get_doc("Shipping Book", cif.inv_no)
    cus_name= frappe.db.get_value("Customer", sb.customer, "customer")
    noti_name= frappe.db.get_value("Notify", sb.notify, "notify")
    category_name= frappe.db.get_value("Product Category", cif.category, "product_category")
    acc_com= frappe.db.get_value("Company", cif.accounting_company, "company_code")
    shi_com= frappe.db.get_value("Company", sb.company, "company_code")
    data = {
        "inv_no": cif.inv_no,
        "inv_date": cif.inv_date,
        "customer": cus_name,
        "category": category_name,
        "notify": noti_name,
        "accounting_company": acc_com,
        "shipping_company": shi_com,
        "handling_charges":cif.handling_charges,
        "insurance":cif.insurance,
        "sales":cif.sales,
        "multiple_sc":cif.multiple_sc if cif.multiple_sc else 0,
        "sc_no":cif.sc_no,
        "product_details": [
            {
                "name": d.name,
                "product": d.product,
                "qty": d.qty,
                "unit": d.unit,
                "sc_no": d.sc_no if d.sc_no else "",
                "rate":d.rate,
                "currency":d.currency,
                "ex_rate":d.ex_rate,
                "charges":d.charges,
                "charges_amount":d.charges_amount,
                "round_off_usd":d.round_off_usd
            }
            for d in cif.product_details
        ],
        "expenses": [
            {
                "name": e.name,
                "expenses": e.expenses,
                "amount":e.amount,
                "currency":e.currency,
                "ex_rate":e.ex_rate
            }
            for e in cif.expenses
        ] if cif.expenses else []
    }
    # frappe.msgprint('expenses')
    return data

@frappe.whitelist()
def get_available_inv_no(doctype, txt, searchfield, start, page_len, filters):
    used_inv = frappe.get_all("Cost Sheet", pluck="inv_no")

    if used_inv:
        placeholders = ', '.join(['%s'] * len(used_inv))
        condition = f"WHERE name NOT IN ({placeholders}) AND invoice_no LIKE %s"
        values = used_inv + [f"%{txt}%"]
    else:
        condition = "WHERE invoice_no LIKE %s"
        values = [f"%{txt}%"]

    values += [page_len, start]

    return frappe.db.sql(f"""
        SELECT name, invoice_no
        FROM `tabCIF Sheet`
        {condition}
        ORDER BY invoice_no ASC
        LIMIT %s OFFSET %s
    """, tuple(values))

def validate_unique_expenses(doc):
        seen = set()
        for row in doc.expenses:
            if row.expenses in seen:
                frappe.throw(_('Expenses must be unique: {0}').format(row.expenses))
            seen.add(row.expenses)

def set_calculated_fields(doc):
    invoice = frappe.db.get_value(
        "CIF Sheet",
        {"name": doc.inv_no},
        ["invoice_no", "load_port", "destination_port", "final_destination"],
        as_dict=True
    )
    doc.custom_title =invoice.invoice_no
    doc.load_port= invoice.load_port
    doc.destination_port= invoice.destination_port
    doc.final_destination= invoice.final_destination



class CostSheet(Document):
    def validate(self):
        validate_unique_expenses(self)
    def before_save(self):
        set_calculated_fields(self)
    


# To Prepare Cost Sheet PDF
@frappe.whitelist()
def render_cost_sheet_pdf(inv_name, pdf=0):
    cost_id = frappe.db.get_value("Cost Sheet", {"inv_no": inv_name}, "name")
    doc = frappe.get_doc("Cost Sheet", cost_id)
    cif_doc= frappe.get_doc("CIF Sheet", doc.inv_no)
    sb= frappe.get_doc("Shipping Book", cif_doc.inv_no)
    doc.customer_name=frappe.db.get_value("Customer", sb.customer, "customer")
    doc.notify_name=frappe.db.get_value("Notify", sb.notify, "notify")
    doc.acc_com_name = frappe.db.get_value("Company", cif_doc.accounting_company, "company_code")
    doc.category_name=frappe.db.get_value("Product Category", cif_doc.category, "product_category")
    doc.load_port_name=frappe.db.get_value("Port", cif_doc.load_port, "port")
    doc.f_country_name=frappe.db.get_value("Port", cif_doc.load_port, "country")
    doc.notify_city=frappe.db.get_value("Notify", sb.notify, "city")
    doc.t_country_name=frappe.db.get_value("City", doc.notify_city, "country")
    doc.destination_port_name=frappe.db.get_value("Port", cif_doc.destination_port, "port")
    doc.agent_name=frappe.db.get_value("Comm Agent", doc.agent, "agent_name")
    doc.sales= cif_doc.sales
    profit= cif_doc.sales- doc.cost
    profit_pct= round(profit/cif_doc.sales,2)
    doc.profit=profit
    doc.profit_pct= profit_pct

    product =  frappe.db.sql("""
        SELECT p.parent, pg.product_group, pro.product, p.po_no, p.qty, u.unit, p.rate, p.currency, p.ex_rate, 
            p.charges, p.charges_amount, p.gross, p.gross_usd 
        FROM `tabProduct Cost` p 
        LEFT JOIN `tabUnit` u ON p.unit = u.name 
        LEFT JOIN `tabProduct` pro ON p.product = pro.name 
        LEFT JOIN `tabProduct Group` pg ON pro.product_group = pg.name 
        WHERE p.parent = %s""", cost_id, as_dict=1)
    product = sorted(product, key=lambda x: x['product_group'])
    exp = frappe.db.sql("""
        SELECT 
            parent,
            amount,
            currency,
            expenses,
            amount_usd AS total_amount 
        FROM `tabExpenses Cost`
        WHERE parent = %s
    """, (cost_id,), as_dict=1)
    # exp_dict = {i.expenses: i.total_amount for i in exp}
    # expenses = {e: exp_dict.get(e, 0) for e in ["Freight", "Local Exp", "Inland Charges", "Switch B/L Charges", "Others", "Insurance"]}

    exp_dict = {
        i.expenses: {
            "amount": i.amount,
            "currency": i.currency,
            "total_amount": i.total_amount
        }
        for i in exp
    }
    expenses = {e: exp_dict.get(e, 0) for e in ["Freight", "Local Exp", "Inland Charges", "Switch B/L Charges", "Insurance", "Others"]}

    context = {
        "doc": doc,
        "product":product,
        "expenses":expenses,
        "generated_date": now_datetime().strftime("%Y-%m-%d %H:%M:%S"),
        "custom_message": "Generated from Python",
        "formatted_date": frappe.format_value(doc.inv_date, {"fieldtype": "Date"})
    }
    html = frappe.render_template("ssd_app/templates/includes/cost_sheet_pdf.html", context)
    if (pdf):
        frappe.local.response.filename = f"CIF_{inv_name}.pdf"
        frappe.local.response.filecontent = get_pdf(html)
        frappe.local.response.type = "pdf"

    else:
        return html