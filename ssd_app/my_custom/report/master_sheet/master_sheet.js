// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["Master Sheet"] = {
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        // 🔗 Clickable inv_no with modal
        if (column.fieldname === "inv_no" && data && data.name) {
            return `<a href="#" onclick="showCIFDetails('${data.name}', '${data.inv_no}'); return false;">${data.inv_no}</a>`;
        }

        return value;
    },
    "filters": [
		{
			"fieldname": "limit",
			"label": "Rows Per Page",
			"fieldtype": "Select",
			"options": "20\n100\n500\n2500",
			"default": "100"
		},
        {
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "default": "2025-01-01",
            "reqd": 0
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 0
        }
        
    ]
}
