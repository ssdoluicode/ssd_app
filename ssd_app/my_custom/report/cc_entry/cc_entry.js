// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["CC Entry"] = {
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

		if (column.fieldname === "action" && data && data.name && data.details != 1) {

			// Escape single quotes for safe JS embedding
			const cc_rec_id = (data.name + "").replace(/'/g, "\\'");

			return `
				${value}
				<a href="#"
				title="Create CC Received Details for ${cc_rec_id}"
				style="margin-left:6px; color:#007bff; text-decoration:none;"
				onclick="
						frappe.route_options = { cc_received_id: '${cc_rec_id}' };
						frappe.set_route('Form', 'CC Received Details', 'new-cc-received-details');
						return false;
				">
				<i class="fa fa-plus-circle"></i>
				</a>
			`;
		}

		return value;
	}

    
};
