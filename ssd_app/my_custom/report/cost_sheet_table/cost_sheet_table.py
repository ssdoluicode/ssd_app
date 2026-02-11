import frappe
from frappe.utils import formatdate, flt
from frappe.utils.pdf import get_pdf
from frappe.utils.jinja import render_template
from frappe import _

def get_cif_data(filters):
    year = filters.year

    if not year:
        max_year = frappe.db.sql("""
            SELECT MAX(YEAR(inv_date))
            FROM `tabCost Sheet`
            WHERE inv_date IS NOT NULL
        """, as_list=True)[0][0]
        conditional_filter= f"WHERE YEAR(cost.inv_date)= {int(max_year)}"
    elif year == "All":
        conditional_filter= ""
    else:
        conditional_filter= f"WHERE YEAR(cost.inv_date)= {int(year)}"

    data= frappe.db.sql(f"""
    SELECT
    cif.name AS cif_id,
    cost.custom_title AS inv_no,
    cost.name,
    cif.inv_date,
    com.company_code AS a_com,
    cat.product_category,
    cus.code AS customer,
    noti.code AS notify,
    cost.commission,
    cost.purchase,
    cif.sales,
    cif.document,     
    cost.cost,
    IFNULL(cif.sales, 0) - IFNULL(cost.cost, 0) AS profit,
    ROUND((IFNULL(cif.sales, 0) - IFNULL(cost.cost, 0)) / NULLIF(cost.cost, 0) * 100, 2) AS profit_pct,        
    IFNULL(exp.freight, 0) AS freight,
    IFNULL(exp.local_exp, 0) AS local_exp,
    l_port.port AS load_port,
    d_port.port AS destination_port,
    l_port.country AS from_country,
    city.country AS to_country,                
    COALESCE(NULLIF(sup.supplier, ''), '**Multi Supplier**') AS supplier
    FROM `tabCost Sheet` cost
    LEFT JOIN `tabCIF Sheet` cif ON cif.name= cost.inv_no
    LEFT JOIN `tabCompany` com ON cif.accounting_company = com.name
    LEFT JOIN `tabShipping Book` sb ON sb.name= cif.inv_no
    LEFT JOIN `tabCustomer` cus ON sb.customer = cus.name
    LEFT JOIN `tabProduct Category` cat ON cif.category = cat.name
    LEFT JOIN `tabNotify` noti ON sb.notify = noti.name
    LEFT JOIN `tabPort` l_port ON cost.load_port= l_port.name
    LEFT JOIN `tabPort` d_port ON cost.destination_port= d_port.name
    LEFT JOIN `tabCity` city ON noti.city=city.name
    LEFT JOIN `tabSupplier` sup ON cost.supplier = sup.name
    LEFT JOIN `tabComm Agent` ca ON ca.name= cost.agent
    LEFT JOIN `tabPayment Term` pt ON pt.name=sb.payment_term
    LEFT JOIN (
        SELECT 
        parent,
        SUM(CASE WHEN expenses = 'Freight' THEN amount ELSE 0 END) AS freight,
        SUM(CASE WHEN expenses = 'Local Exp' THEN amount ELSE 0 END) AS local_exp,
        SUM(CASE WHEN expenses = 'Inland Charges' THEN amount ELSE 0 END) AS inland_charges,
        SUM(CASE WHEN expenses = 'Switch B/L Charges' THEN amount ELSE 0 END) AS switch_bl_charges,
        SUM(CASE WHEN expenses = 'Insurance' THEN amount ELSE 0 END) AS insurance,
        SUM(CASE WHEN expenses = 'Others' THEN amount ELSE 0 END) AS others
        FROM `tabExpenses Cost`
        GROUP BY parent
    ) AS exp ON exp.parent= cost.name
    {conditional_filter}
    ORDER BY cost.creation DESC 
    ;
    """, as_dict=1)
    return data


def execute(filters=None):
    # filters = filters or {}

    columns = [
        # {"label": "Inv ID", "fieldname": "name", "fieldtype": "Data", "width": 80},
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data"},
        {"label": "Inv Date", "fieldname": "inv_date", "fieldtype": "Date"},
        {"label": "Com", "fieldname": "a_com", "fieldtype": "Data","width": 100},
        {"label": "Category", "fieldname": "product_category", "fieldtype": "Data", "width": 150},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 150},
        {"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 180},
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 180},
        {"label": "Purchase", "fieldname": "purchase", "fieldtype": "Float", "width": 110},
        {"label": "Freight", "fieldname": "freight", "fieldtype": "Float", "width": 100},
        {"label": "Local Exp", "fieldname": "local_exp", "fieldtype": "Float", "width": 90},
        {"label": "Comm", "fieldname": "commission", "fieldtype": "Float", "width": 90},
        {"label": "Cost", "fieldname": "cost", "fieldtype": "Float", "width": 120},
        {"label": "Profit", "fieldname": "profit", "fieldtype": "Float", "width": 90},
        {"label": "Profit %", "fieldname": "profit_pct", "fieldtype": "Float", "width": 80},
        {"label": "Sales", "fieldname": "sales", "fieldtype": "Float", "width": 120},
        
    ]
    data = get_cif_data(filters)
    return columns, data


@frappe.whitelist()
def get_years():
    years = frappe.db.sql("""
        SELECT DISTINCT YEAR(inv_date) AS year
        FROM `tabCost Sheet`
        WHERE inv_date IS NOT NULL
        ORDER BY year ASC
    """, as_dict=True)

    # Return a simple list of years as strings
    return [str(d.year) for d in years]
