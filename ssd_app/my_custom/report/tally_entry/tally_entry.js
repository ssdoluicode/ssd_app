// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["Tally Entry"] = {
	onload: function(report) {
        // Add a custom button to the report menu/toolbar
		if(frappe.session.user == "Administrator"){
			 report.page.add_inner_button(__("Generate Tally XML"), function() {
            // Get values from all filters
            let filters = report.get_values();

            // Validate that required fields are filled before sending
            if (!filters.company || !filters.from_date || !filters.to_date) {
                frappe.msgprint(__("Please select Company, From Date, and To Date filters."));
                return;
            }

            // Call the Python backend method
            frappe.call({
                method: "ssd_app.utils.tally_xml.create_tally_xml.create_tally_xml",
                args: {
                    filters: filters
                },
                freeze: true,
                freeze_message: __("Generating Tally XML..."),
        
				callback: async function (r) { // Added 'async' keyword here
					if (
						r.message &&
						r.message.status === "success" &&
						Array.isArray(r.message.data_context) &&
						r.message.data_context.length > 0
					) {
						// Helper function for the 1-second delay
						const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

						// Changed from .forEach to a sequential for...of loop to support sleep tracking
						for (const item of r.message.data_context) {
							try {
								// Skip empty data
								if (!item.data) {
									continue; // Changed 'return' to 'continue' for loop compatibility
								}

								// Ensure XML content is a string
								const xmlContent = typeof item.data === "string"
									? item.data.trim()
									: String(item.data);

								if (!xmlContent) {
									continue;
								}

								// Safe filename
								let fileName = item.file_name || "tally_export";
								fileName = fileName.replace(/[<>:"/\\|?*\x00-\x1F]/g, "_");

								if (!fileName.toLowerCase().endsWith(".xml")) {
									fileName += ".xml";
								}

								// Create XML Blob
								const blob = new Blob([xmlContent], {
									type: "application/xml;charset=utf-8"
								});

								// Download
								const url = window.URL.createObjectURL(blob);
								const link = document.createElement("a");

								link.href = url;
								link.download = fileName;
								link.style.display = "none";

								document.body.appendChild(link);
								link.click();

								// Immediate clean up for this iteration (safe because loop waits)
								document.body.removeChild(link);
								window.URL.revokeObjectURL(url);

								// Success message
								if (item.alert_msg) {
									frappe.show_alert({
										message: __(item.alert_msg),
										indicator: "green"
									});
								}

								// Sleep for exactly 1 second before allowing the next loop item to download
								await sleep(1000);

							} catch (err) {
								console.error("XML download failed:", err);

								frappe.msgprint({
									title: __("Download Error"),
									message: __("Unable to download {0}.", [item.file_name || "XML file"]),
									indicator: "red"
								});
							}
						}
					} else {
						frappe.msgprint(__("No records compiled for the selected filters. File generation stopped."));
					}
				}
            });
        });

		}
       
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
