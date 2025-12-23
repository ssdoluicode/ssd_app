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

def get_data(filters):
    group_by = filters.get("group_by")
    conditions = get_conditions(filters)

    if group_by == "Customer":
        query = f"""
            SELECT
                si.customer,
                SUM(si.sales) AS total
            FROM `tabCIF Sheet` si
            WHERE {conditions}
            GROUP BY si.customer
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

    else:  # Date-wise
        query = f"""
            SELECT
                si.inv_date AS posting_date,
                SUM(si.sales) AS total
            FROM `tabCIF Sheet` si
            WHERE {conditions}
            GROUP BY si.inv_date
            ORDER BY si.inv_date
        """
    print(query)
    print(filters)

    return frappe.db.sql(query, filters, as_dict=True)


def get_chart(data, filters):
    # data = get_data(filters)
    print(data)

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


def get_conditions(filters):
    conditions = "1 = 1"

    if filters.get("customer"):
        conditions += " AND si.customer = %(customer)s"

    conditions += " AND si.inv_date BETWEEN %(from_date)s AND %(to_date)s"

    return conditions


def execute(filters=None):
    filters = filters or {}

    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart(data, filters)

    return columns, data, None, chart
