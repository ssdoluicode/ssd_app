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
            FROM `tabCIF Sheet`
            WHERE inv_date IS NOT NULL
        """, as_list=True)[0][0]
        conditional_filter= f"""WHERE YEAR(cif.inv_date)= {int(max_year)}"""
    elif year == "All":
        conditional_filter= ""
    else:
        conditional_filter= f"""WHERE YEAR(cif.inv_date)= {int(year)}"""
   

    data= frappe.db.sql(f"""
        SELECT
    cif.invoice_no AS inv_no,
    sb.name,
    cif.inv_date,
    com.company_code AS a_com,
    cat.product_category,
    cus.code AS customer,
    noti.code AS notify,
    cif.insurance,
    cif.gross_sales,
    cif.handling_pct,
    cif.handling_charges,
    cif.sales,
    cif.document,
    cif.cc,
    l_port.port AS load_port,
    d_port.port AS destination_port,
    l_port.country AS from_country,
    city.country AS to_country,
                    
    CASE
    WHEN cost.inv_no IS NULL THEN ''
    ELSE COALESCE(sup.supplier, '--Multi--')
    END AS supplier,
    bank.bank,
    IF(sb.payment_term IN ('LC', 'DA'),
       CONCAT(cif.payment_term, '- ', cif.term_days),
       cif.payment_term) AS p_term,
    cif.from_date,
    cif.due_date,
    cif.bank_ref_no,
    CASE
        WHEN cif.payment_term = 'TT' THEN ''
        WHEN COALESCE(t_rec.total_rec, 0) = 0 THEN 'Unpaid'
        WHEN COALESCE(t_rec.total_rec, 0) >= cif.document THEN 'Paid'
        ELSE 'Part'
    END AS status

    FROM `tabCIF Sheet` cif

    LEFT JOIN `tabShipping Book` sb ON sb.name = cif.inv_no
    LEFT JOIN `tabCompany` com ON cif.accounting_company = com.name
    LEFT JOIN `tabCustomer` cus ON sb.customer = cus.name
    LEFT JOIN `tabProduct Category` cat ON cif.category = cat.name
    LEFT JOIN `tabNotify` noti ON sb.notify = noti.name
    LEFT JOIN `tabBank` bank ON sb.bank = bank.name
    LEFT JOIN `tabPort` l_port ON cif.load_port= l_port.name
    LEFT JOIN `tabPort` d_port ON cif.destination_port= d_port.name
    LEFT JOIN `tabCity` city ON noti.city=city.name

    LEFT JOIN (
        SELECT inv_no, MIN(supplier) AS supplier
        FROM `tabCost Sheet`
        GROUP BY inv_no
    ) cost ON cif.name = cost.inv_no
    LEFT JOIN `tabSupplier` sup ON cost.supplier = sup.name

    LEFT JOIN (
        SELECT inv_no, SUM(received) AS total_rec
        FROM `tabDoc Received`
        GROUP BY inv_no
    ) t_rec ON sb.name = t_rec.inv_no
    {conditional_filter}
    ORDER BY cif.creation DESC ;
    """, as_dict=1)
    return data


def execute(filters=None):
    columns = [
        # {"label": "Inv ID", "fieldname": "name", "fieldtype": "Data", "width": 80},
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
        {"label": "Inv Date", "fieldname": "inv_date", "fieldtype": "Date", "width": 110},
        {"label": "Acc Com", "fieldname": "a_com", "fieldtype": "Data", "width": 90},
        {"label": "Category", "fieldname": "product_category", "fieldtype": "Data", "width": 110},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 120},
        {"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 150},
        {"label": "Sales", "fieldname": "sales", "fieldtype": "Float", "width": 100},
        {"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 100},
        {"label": "CC", "fieldname": "cc", "fieldtype": "Float", "width": 100},
        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 60},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 70},
        {"label": "P Term", "fieldname": "p_term", "fieldtype": "Data", "width": 80},
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 180},
    ]
    data = get_cif_data(filters)
    return columns, data



@frappe.whitelist()
def get_years():
    years = frappe.db.sql("""
        SELECT DISTINCT YEAR(inv_date) AS year
        FROM `tabCIF Sheet`
        WHERE inv_date IS NOT NULL
        ORDER BY year ASC
    """, as_dict=True)

    # Return a simple list of years as strings
    return [str(d.year) for d in years]