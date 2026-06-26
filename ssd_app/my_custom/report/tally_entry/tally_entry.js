// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["Tally Entry"] = {
	onload: function(report) {
        // Add a custom button to the report menu/toolbar
        report.page.add_inner_button(__("Generate Tally XML"), function() {
            // Get values from all filters
            let filters = report.get_values();

            // Validate that required fields are filled before sending
            if (!filters.company || !filters.from_date || !filters.to_date) {
                frappe.msgprint(__("Please select Company, From Date, and To Date filters."));
                return;
            }

            // frappe.register_with_user_action_back_button(report);

            // Call the Python backend method
            frappe.call({
                method: "ssd_app.utils.tally_xml.create_tally_xml.create_tally_xml",
                args: {
                    filters: filters
                },
                freeze: true,
                freeze_message: __("Generating Tally XML..."),
                callback: function(r) {
                    if (r.message) {
                        // Option A: If your python method returns a file URL/content to download
                        if (r.message.file_url) {
                            window.open(r.message.file_url);
                        } 
                        // Option B: If it returns a success message
                        else {
							console.log(r.message)
                            frappe.msgprint(__("Tally XML Generated successfully!"));
                        }
                    }
                }
            });
        });
    },
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
				"CC Received",
				"LC Payment",
				"U LC Payment",
				"Import Loan",
				"Import Loan Payment",
				"CC Received",
				"Sales"
			],
			default: ""
		}
	]
};
