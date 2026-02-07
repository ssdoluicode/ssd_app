# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt


import frappe
from frappe.utils import flt


def get_columns(filters):
    group_by = filters.get("group_by")

    if group_by == "Customer":
        return [
            {"label": "Customer", "fieldname": "customer", "width": 200},
            {"label": "Sales Amount", "fieldname": "total", "fieldtype": "Currency", "width": 150},
        ]

    if group_by == "Item":
        return [
            {"label": "Item", "fieldname": "item_code", "width": 200},
            {"label": "Sales Amount", "fieldname": "total", "fieldtype": "Currency", "width": 150},
        ]

    # Default Date-wise
    return [
        {"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": "Sales Amount", "fieldname": "total", "fieldtype": "Currency", "width": 150},
    ]

# def get_data(filters):
#     group_by = filters.get("group_by")
#     conditions = get_conditions(filters)

#     if group_by == "Customer":
#         query = f"""
#             SELECT
#             sb.customer AS customer,
#             SUM(si.sales) AS total
#         FROM `tabCIF Sheet` si
#         LEFT JOIN `tabShipping Book` sb
#             ON sb.name = si.inv_no
#         WHERE {conditions}
#         GROUP BY sb.customer
#         ORDER BY total DESC
#         """

#     elif group_by == "Item":
#         query = f"""
#             SELECT
#                 si.category AS item_code,
#                 SUM(si.sales) AS total
#             FROM `tabCIF Sheet` si
#             WHERE {conditions}
#             GROUP BY si.category
#             ORDER BY total DESC
#         """

#     else:  # Date-wise
#         query = f"""
#             SELECT
#                 si.inv_date AS posting_date,
#                 SUM(si.sales) AS total
#             FROM `tabCIF Sheet` si
#             WHERE {conditions}
#             GROUP BY si.inv_date
#             ORDER BY si.inv_date
#         """
#     print(query)
#     print(filters)

#     return frappe.db.sql(query, filters, as_dict=True)

def get_data(filters):
    group_by = filters.get("group_by")
    conditions = get_conditions(filters, group_by)

    if group_by == "Customer":
        query = f"""
            SELECT
                sb.customer AS customer,
                SUM(si.sales) AS total
            FROM `tabCIF Sheet` si
            LEFT JOIN `tabShipping Book` sb ON sb.name = si.inv_no
            WHERE {conditions}
            GROUP BY sb.customer
            ORDER BY total DESC
        """

    elif group_by == "Item":
        query = f"""
            SELECT
                si.category AS item_code,
                SUM(si.sales) AS total
            FROM `tabCIF Sheet` si
            WHERE {conditions}
            GROUP BY si.category
            ORDER BY total DESC
        """

    else:
        query = f"""
            SELECT
                si.inv_date AS posting_date,
                SUM(si.sales) AS total
            FROM `tabCIF Sheet` si
            WHERE {conditions}
            GROUP BY si.inv_date
            ORDER BY si.inv_date
        """

    return frappe.db.sql(query, filters, as_dict=True)



def get_chart(data, filters):
    # data = get_data(filters)

    labels = []
    values = []

    group_by = filters.get("group_by")
    chart_type = filters.get("chart_type") or "line"

    for row in data:
        if group_by == "Customer":
            labels.append(row.customer)
        elif group_by == "Item":
            labels.append(row.item_code)
        else:
            labels.append(row.posting_date)

        values.append(flt(row.total))
    x= {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Sales",
                    "values": values
                }
            ]
        },
        "type": chart_type,
        "height": 320
    }
    print(x)

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Sales",
                    "values": values
                }
            ]
        },
        "type": chart_type,
        "height": 320
    }


# def get_conditions(filters):
#     conditions = "1 = 1"

#     if filters.get("customer"):
#         conditions += " AND sb.customer = %(customer)s"

#     conditions += " AND si.inv_date BETWEEN %(from_date)s AND %(to_date)s"

#     return conditions

def get_conditions(filters, group_by):
    conditions = []

    # Date filter (always applicable)
    if filters.get("from_date") and filters.get("to_date"):
        conditions.append(
            "si.inv_date BETWEEN %(from_date)s AND %(to_date)s"
        )

    # Customer filter ONLY when Shipping Book is joined
    if filters.get("customer") and group_by == "Customer":
        conditions.append(
            "sb.customer = %(customer)s"
        )

    return " AND ".join(conditions) or "1 = 1"



def execute(filters=None):
    filters = filters or {}

    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart(data, filters)

    return columns, data, None, chart
