
// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["Import Banking"] = {
	onload: function (report) {
		// report.page.add_inner_button("New LC Open", function () {
        //     frappe.new_doc("LC Open");
        // });
		report.page.add_inner_button("New LC Open", function () {
			frappe.new_doc("LC Open", true);
		}, "New");

		report.page.add_inner_button("New Cash Loan", function () {
			frappe.new_doc("Cash Loan", true);
		}, "New");
	},


	"filters": [
		{
            fieldname: "based_on",
            label: "Based On",
            fieldtype: "Select",
            options: "All\nCurrent Position\nLC Open\nUsance LC\nImport Loan\nCash Loan",
            default: "Current Position",
            reqd: 1
        },
        {
            fieldname: "as_on",
            label: "As On",
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        }

	]
};

