// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Report Chart"] = {
	filters: [
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            fieldname: "customer",
            label: "Customer",
            fieldtype: "Link",
            options: "Customer"
        },
        {
            fieldname: "group_by",
            label: "Group By",
            fieldtype: "Select",
            options: [
                { label: "Date", value: "Date" },
                { label: "Customer", value: "Customer" },
                { label: "Item", value: "Item" }
            ],
            default: "Date"
        },
        {
            fieldname: "chart_type",
            label: "Chart Type",
            fieldtype: "Select",
            options: [
                { label: "Line", value: "line" },
                { label: "Bar", value: "bar" },
                { label: "Pie", value: "pie" }
            ],
            default: "line"
        }
    ]
};
