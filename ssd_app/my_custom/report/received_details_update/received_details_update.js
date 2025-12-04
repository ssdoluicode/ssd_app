// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["Received Details Update"] = {
	 "filters": [
        {
            "fieldname": "status",
            "label": __("Status"),
            "fieldtype": "Select",
            "options": ["All", "Updated", "Pending"],
            "default": "Pending",
            "reqd": 1
        }
    ],
	formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "inv_no" && data && data.inv_no && data.nego_details != 1) {
            const doctype = "Doc Received Details";
            const inv_no = String(data.name).replace(/'/g, "\\'");

            return `
                ${value}
                <a href="#"
                   title="Create ${doctype} for ${inv_no}"
                   style="margin-left:6px; color:#007bff; text-decoration:none;"
                   onclick="frappe.route_options = { inv_no: '${inv_no}' }; frappe.set_route('Form', '${doctype}', 'new-${doctype}'); return false;">
                   <i class="fa fa-plus-circle"></i>
                </a>`;
        }

        return value;
    }
};
