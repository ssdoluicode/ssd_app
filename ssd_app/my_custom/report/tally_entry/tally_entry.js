// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["Tally Entry"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
			reqd: 1
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			get_query: function () {
				return {
					filters: {
						"company_code": ["!=", ""]
					}
				};
			},
			reqd: 1
		},
		{
			fieldname: "entry_for",
			label: __("Entry For"),
			fieldtype: "Select",
			options: [
				"",
				"Doc Nego",
				"Doc Refund",
				"Doc Received",
				"Interest Payment",
				"LC Payment",
				"U LC Payment",
				"Import Loan",
				"Import Loan Payment",
				"CC Received"
			],
			default: ""
		}
	]
};
