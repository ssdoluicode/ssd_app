# Copyright (c) 2026, SSDolui and contributors
# For license information, please see license.txt

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
        conditional_filter= f"""AND YEAR(cost.inv_date)= {int(max_year)}"""
    elif year == "All":
        conditional_filter= ""
    else:
        conditional_filter= f"""AND YEAR(cost.inv_date)= {int(year)}"""

    data= frappe.db.sql(f"""
    SELECT
    cif.name AS cif_id,
    cost.custom_title AS inv_no,
    cost.name,
    cif.inv_date,
    cat.product_category,
    cus.code AS customer,
    noti.code AS notify,
    qty.qty,
    cost.commission,
    cost.comm_based_on,
    cost.comm_rate,
    ca.agent_name AS agent,
    cost.purchase,
    cif.sales,
    cif.document,
    CASE
        WHEN pt.direct_to_supplier = 1 THEN cif.document
        ELSE COALESCE(d_rec.doc_rec, 0)
    END AS doc_rec,      
    cost.cost,
    IFNULL(cif.sales, 0) - IFNULL(cost.cost, 0) AS profit,
    l_port.port AS load_port,
    d_port.port AS destination_port,
    l_port.country AS from_country,
    city.country AS to_country,                
    cp.comm_paid,
    cp.paid_date
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
    LEFT JOIN `tabComm Agent` ca ON ca.name= cost.agent
    LEFT JOIN `tabPayment Term` pt ON pt.name=sb.payment_term
    LEFT JOIN (
                SELECT 
					t.parent,
					GROUP_CONCAT(
						CONCAT(FORMAT(t.total_qty, 0), ' ', t.unit_display)
						ORDER BY t.unit_display
						SEPARATOR ', '
					) AS qty
				FROM (
					SELECT 
						pc.parent,
						pc.unit,
						u.unit AS unit_display,
						SUM(pc.qty) AS total_qty
					FROM `tabProduct Cost` pc
					LEFT JOIN `tabUnit` u 
						ON pc.unit = u.name
					GROUP BY pc.parent, pc.unit, u.unit
				) t
				GROUP BY t.parent
				ORDER BY t.parent
                        
    ) qty on cost.name= qty.parent
    LEFT JOIN (
        SELECT inv_no, SUM(received) AS doc_rec
        FROM `tabDoc Received`
        GROUP BY inv_no
    ) d_rec ON sb.name = d_rec.inv_no
    LEFT JOIN (
			SELECT 
			cb.inv_no,
			SUM(cb.amount) AS comm_paid,
			MAX(cp.date) AS paid_date
		FROM `tabComm Breakup` cb
		LEFT JOIN `tabComm Paid` cp 
			ON cp.name = cb.parent
		GROUP BY cb.inv_no
		ORDER BY cb.inv_no
    ) AS cp ON cp.inv_no= cost.name
    WHERE  cost.commission > 0
    {conditional_filter}
    
    ORDER BY cost.creation DESC 
    ;
    """, as_dict=1)
    return data


def execute(filters=None):
    # filters = filters or {}

    columns = [
        # {"label": "Inv ID", "fieldname": "name", "fieldtype": "Data", "width": 80},
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data","width": 90},
        {"label": "Inv Date", "fieldname": "inv_date", "fieldtype": "Date", "width": 110},
        {"label": "Category", "fieldname": "product_category", "fieldtype": "Data", "width": 120},
        # {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 150},
        {"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 170},
        {"label": "Sales", "fieldname": "sales", "fieldtype": "Float", "width": 120},
        {"label": "Cost", "fieldname": "cost", "fieldtype": "Float", "width": 120},
        {"label": "Purchase", "fieldname": "purchase", "fieldtype": "Float", "width": 110},
        {"label": "Profit", "fieldname": "profit", "fieldtype": "Float", "width": 90},
        {"label": "Qty", "fieldname": "qty", "fieldtype": "Data", "width": 90},
        {"label": "Based On", "fieldname": "comm_based_on", "fieldtype": "Data", "width": 90},
        {"label": "Rate", "fieldname": "comm_rate", "fieldtype": "float", "width": 70},
        {"label": "Agent", "fieldname": "agent", "fieldtype": "Data", "width": 90},
        {"label": "Comm", "fieldname": "commission", "fieldtype": "Float", "width": 90},
        {"label": "Status", "fieldname": "comm_status", "fieldtype": "Data", "width": 90},
        {"label": "Paid On", "fieldname": "paid_date", "fieldtype": "Date", "width": 110},
        # {"label": "Comm Paid", "fieldname": "comm_paid", "fieldtype": "Float"}
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

