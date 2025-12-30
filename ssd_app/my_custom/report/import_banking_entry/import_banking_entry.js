// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["Import Banking Entry"] = {
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
            "options": ["All", "LC Payment", "U LC Payment", "Imp Loan", "Imp Loan Payment"],
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


        if (column.fieldname === "type" && data && data.details != 1) {
            // const doctype = "Doc Nego Details";
            let doctype = "";
			let id="";
            if (data.type === "LC Payment") {
                doctype = "LC Payment Details";
				id="import_loan_id";
            } else if (data.type === "U LC Payment") {
                doctype = "Usance LC Payment Details";
				id="lc_payment_id";
            } else if (data.type === "Imp Loan") {
                doctype = "Import Loan Details";
				id="import_loan_id";
			} else if (data.type === "Imp Loan Payment") {
                doctype = "Import Loan Payment Details";
				id="import_loan_id";
            } else {
                return value;  // If no valid type, do nothing
            }

            const inv_no = data.name;

            return `
                ${value}
                <a href="#"
                   title="Create ${doctype} for ${inv_no}"
                   style="margin-left:6px; color:#007bff; text-decoration:none;"
                   onclick="frappe.route_options = { ${id}: '${inv_no}' }; frappe.set_route('Form', '${doctype}', 'new-${doctype}'); return false;">
                   <i class="fa fa-plus-circle"></i>
                </a>`;
        }

        return value;
    }
};
	