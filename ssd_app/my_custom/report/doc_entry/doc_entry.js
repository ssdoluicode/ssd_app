// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["Doc Entry"] = {
	"filters": [
        {
            "fieldname": "status",
            "label": __("Status"),
            "fieldtype": "Select",
            "options": ["All", "Updated", "Pending"],
            "default": "Pending",
            "reqd": 1
        },
        {
            "fieldname": "type",
            "label": __("Type"),
            "fieldtype": "Select",
            "options": ["All", "Nego", "Refund", "Received"],
            "default": "All",
            "reqd": 1
        }
    ],
    

    onload: function(report) {
        report.page.add_inner_button(
            "New Interest Paid",
            function () {
                frappe.set_route("Form", "Interest Paid", "new-Interest Paid");
            }
        );
    },

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "document" && data?.shi_id) {
            return `<a style="color:blue;"  href="#" onclick="showDocFlow('${data.shi_id}', '${data.inv_no}'); return false;">${Number(data.document).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</a>`;
        }

        if (column.fieldname === "inv_no" && data?.cif_id) {
            return `<a style="color:blue;" href="#" onclick="showCIFDetails('${data.cif_id}', '${data.inv_no}'); return false;">${data.inv_no}</a>`;
        }

        if (column.fieldname === "type" && data && data.inv_no && data.details != 1) {
            // const doctype = "Doc Nego Details";
            let doctype = "";
            if (data.type === "Nego") {
                doctype = "Doc Nego Details";
            } else if (data.type === "Refund") {
                doctype = "Doc Refund Details";
            } else if (data.type === "Received") {
                doctype = "Doc Received Details";
            } else {
                return value;  // If no valid type, do nothing
            }

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
	