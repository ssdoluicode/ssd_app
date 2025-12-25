# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.pdf import get_pdf
from frappe.utils import now_datetime, flt
from frappe import _

class CIFSheet(Document):
    def before_save(self):
        self.set_countries()

    def validate(self):
        self.validate_unique_expenses()

    def set_countries(self):
        """Fetches country data for ports and destinations"""
        if self.load_port:
            self.from_country = frappe.db.get_value("Port", self.load_port, "country")
        if self.final_destination:
            self.to_country = frappe.db.get_value("City", self.final_destination, "country")

    def validate_unique_expenses(self):
        seen = set()
        for row in self.expenses:
            if row.expenses in seen:
                frappe.throw(_('Expenses must be unique: {0}').format(row.expenses))
            seen.add(row.expenses)

@frappe.whitelist()
def render_cif_sheet_pdf(inv_name, pdf=0):
    doc = frappe.get_doc("CIF Sheet", inv_name)
    
    # Map display names efficiently
    doc.customer_name = frappe.db.get_value("Customer", doc.customer, "name") # Fixed 'customer_name' column error
    doc.notify_name = frappe.db.get_value("Notify", doc.notify, "notify")
    doc.acc_com_name = frappe.db.get_value("Company", doc.accounting_company, "company_code")
    doc.category_name = frappe.db.get_value("Product Category", doc.category, "product_category")
    doc.bank_name = frappe.db.get_value("Bank", doc.bank, "bank")
    doc.load_port_name = frappe.db.get_value("Port", doc.load_port, "port")
    doc.f_country_name = frappe.db.get_value("Port", doc.load_port, "country")
    doc.notify_city = frappe.db.get_value("Notify", doc.notify, "city")
    doc.t_country_name = frappe.db.get_value("City", doc.notify_city, "country")
    doc.destination_port_name = frappe.db.get_value("Port", doc.destination_port, "port")

    product = frappe.db.sql("""
        SELECT p.parent, pg.product_group, pro.product, p.sc_no, p.qty, u.unit, p.rate, p.currency, p.ex_rate, 
            p.charges, p.charges_amount, p.gross, p.gross_usd 
        FROM `tabProduct CIF` p 
        LEFT JOIN `tabUnit` u ON p.unit = u.name 
        LEFT JOIN `tabProduct` pro ON p.product = pro.name 
        LEFT JOIN `tabProduct Group` pg ON pro.product_group = pg.name 
        WHERE p.parent = %s""", inv_name, as_dict=1)
    product = sorted(product, key=lambda x: x['product_group'])

    exp = frappe.get_all("Expenses CIF", filters={'parent': inv_name}, 
                         fields=['expenses', 'amount', 'currency', 'amount_usd as total_amount'])
    
    exp_dict = {i.expenses: i for i in exp}
    expenses = {e: exp_dict.get(e, 0) for e in ["Freight", "Local Exp", "Inland Charges", "Switch B/L Charges", "Others"]}

    context = {
        "doc": doc,
        "product": product,
        "expenses": expenses,
        "generated_date": now_datetime().strftime("%Y-%m-%d %H:%M:%S"),
        "custom_message": "Generated from Python",
        "formatted_date": frappe.format_value(doc.inv_date, {"fieldtype": "Date"})
    }
    
    html = frappe.render_template("ssd_app/templates/includes/cif_sheet_pdf.html", context)
    if int(pdf):
        frappe.local.response.filename = f"CIF_{inv_name}.pdf"
        frappe.local.response.filecontent = get_pdf(html)
        frappe.local.response.type = "pdf"
    else:
        return html

@frappe.whitelist()
def render_master_sheet_pdf(inv_name, pdf=0):
    cost_name = frappe.db.get_value("Cost Sheet", {"inv_no": inv_name}, "name")
    doc = frappe.get_doc("CIF Sheet", inv_name)
    
    # Set display properties
    doc.customer_name = frappe.db.get_value("Customer", doc.customer, "name")
    doc.notify_name = frappe.db.get_value("Notify", doc.notify, "notify")
    doc.acc_com_name = frappe.db.get_value("Company", doc.accounting_company, "company_code")
    doc.category_name = frappe.db.get_value("Product Category", doc.category, "product_category")
    doc.bank_name = frappe.db.get_value("Bank", doc.bank, "bank")
    doc.load_port_name = frappe.db.get_value("Port", doc.load_port, "port")
    doc.f_country_name = frappe.db.get_value("Port", doc.load_port, "country")
    doc.notify_city = frappe.db.get_value("Notify", doc.notify, "city")
    doc.t_country_name = frappe.db.get_value("City", doc.notify_city, "country")
    doc.destination_port_name = frappe.db.get_value("Port", doc.destination_port, "port")
    
    if cost_name:
        cost_sheet = frappe.db.get_value("Cost Sheet", cost_name, ["purchase", "commission", "comm_rate", "agent", "cost", "profit", "profit_pct"], as_dict=1)
        doc.purchase = cost_sheet.purchase or 0
        doc.comm = cost_sheet.commission or 0
        doc.comm_rate = cost_sheet.comm_rate or 0
        doc.comm_agent = frappe.db.get_value("Comm Agent", cost_sheet.agent, "agent_name") if cost_sheet.agent else ""
        doc.cost = cost_sheet.cost or 0
        doc.profit = cost_sheet.profit or 0
        doc.profit_pct = cost_sheet.profit_pct or 0

    product = frappe.db.sql("""
        SELECT p.parent, pg.product_group, pro.product, p.sc_no, p.qty, u.unit, p.rate AS s_rate, p.ex_rate AS s_ex_rate, 
            sc.symbol AS s_curr_s, p.gross_usd AS g_sales_usd, 
            IFNULL(pc.rate,0) AS b_rate, 
            COALESCE(bc.symbol, '') AS b_curr_s,
            IFNULL(pc.ex_rate, 0) AS b_ex_rate, 
            IFNULL(pc.gross_usd, 0) AS pur_usd
        FROM `tabProduct CIF` p 
        LEFT JOIN `tabUnit` u ON p.unit = u.name 
        LEFT JOIN `tabProduct` pro ON p.product = pro.name 
        LEFT JOIN `tabProduct Group` pg ON pro.product_group = pg.name 
        LEFT JOIN `tabCurrency` sc ON p.currency = sc.name
        LEFT JOIN `tabProduct Cost` pc ON pc.id_code = p.name
        LEFT JOIN `tabCurrency` bc ON pc.currency = bc.name
        WHERE p.parent = %s""", inv_name, as_dict=1)
    product = sorted(product, key=lambda x: x['product_group'])

    # Sales Expenses
    exp = frappe.get_all("Expenses CIF", filters={'parent': inv_name}, fields=['expenses', 'amount', 'currency', 'amount_usd as total_amount'])
    exp_dict = {i.expenses: i for i in exp}
    expenses = {e: exp_dict.get(e, 0) for e in ["Freight", "Local Exp", "Inland Charges", "Switch B/L Charges", "Others"]}

    # Cost Expenses
    cost_expenses = {e: 0 for e in ["Freight", "Local Exp", "Inland Charges", "Switch B/L Charges", "Others"]}
    cost_insurance = 0
    if cost_name:
        c_exp = frappe.get_all("Expenses Cost", filters={'parent': cost_name}, fields=['expenses', 'amount', 'currency', 'amount_usd as total_amount'])
        cost_exp_dict = {}
        for i in c_exp:
            if i.expenses == "Insurance":
                cost_insurance = i.amount
            cost_exp_dict[i.expenses] = i
        cost_expenses = {e: cost_exp_dict.get(e, 0) for e in ["Freight", "Local Exp", "Inland Charges", "Switch B/L Charges", "Others"]}

    context = {
        "doc": doc,
        "product": product,
        "expenses": expenses,
        "cost_expenses": cost_expenses,
        "cost_insurance": cost_insurance,
        "generated_date": now_datetime().strftime("%Y-%m-%d %H:%M:%S"),
        "custom_message": "Generated from Python",
        "formatted_date": frappe.format_value(doc.inv_date, {"fieldtype": "Date"})
    }
    
    html = frappe.render_template("ssd_app/templates/includes/master_sheet_pdf.html", context)
    if int(pdf):
        frappe.local.response.filename = f"Master_{inv_name}.pdf"
        frappe.local.response.filecontent = get_pdf(html)
        frappe.local.response.type = "pdf"
    else:
        return html

@frappe.whitelist()
def check_related_docs(inv_id):
    return bool(frappe.db.exists("Doc Received", {"inv_no": inv_id}) or 
                frappe.db.exists("Doc Nego", {"inv_no": inv_id}))