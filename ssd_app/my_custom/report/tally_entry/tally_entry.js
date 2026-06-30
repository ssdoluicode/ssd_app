// // Copyright (c) 2025, SSDolui and contributors
// // For license information, please see license.txt

// frappe.query_reports["Tally Entry"] = {
// 	onload: function(report) {
//         // Add a custom button to the report menu/toolbar
// 		if(frappe.session.user == "Administrator"){
// 			 report.page.add_inner_button(__("Generate Tally XML"), function() {
//             // Get values from all filters
//             let filters = report.get_values();

//             // Validate that required fields are filled before sending
//             if (!filters.company || !filters.from_date || !filters.to_date) {
//                 frappe.msgprint(__("Please select Company, From Date, and To Date filters."));
//                 return;
//             }

// 			frappe.prompt([
// 				{
// 					label: __('Enter Authorization Code'),
// 					fieldname: 'auth_code',
// 					fieldtype: 'Password', // Use 'Data' if you want the text visible while typing
// 					reqd: 1
// 				}
// 			], function(values) {
// 				// Check if the entered code matches "xml"
// 				if (values.auth_code && values.auth_code.trim().toLowerCase() === "xml") {
                
// 					// --- YOUR CLICK EVENT LOGIC HERE ---
// 					frappe.msgprint(__("Code verified. Generating Tally XML..."));

// 					// Call the Python backend method
// 					frappe.call({
// 						method: "ssd_app.utils.tally_xml.create_tally_xml.create_tally_xml",
// 						args: {
// 							filters: filters
// 						},
// 						freeze: true,
// 						freeze_message: __("Generating Tally XML..."),
				
// 						callback: async function (r) { // Added 'async' keyword here
// 							if (
// 								r.message &&
// 								r.message.status === "success" &&
// 								Array.isArray(r.message.data_context) &&
// 								r.message.data_context.length > 0
// 							) {
// 								// Helper function for the 1-second delay
// 								const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

// 								// Changed from .forEach to a sequential for...of loop to support sleep tracking
// 								for (const item of r.message.data_context) {
// 									try {
// 										// Skip empty data
// 										if (!item.data) {
// 											continue; // Changed 'return' to 'continue' for loop compatibility
// 										}

// 										// Ensure XML content is a string
// 										const xmlContent = typeof item.data === "string"
// 											? item.data.trim()
// 											: String(item.data);

// 										if (!xmlContent) {
// 											continue;
// 										}

// 										// Safe filename
// 										let fileName = item.file_name || "tally_export";
// 										fileName = fileName.replace(/[<>:"/\\|?*\x00-\x1F]/g, "_");

// 										if (!fileName.toLowerCase().endsWith(".xml")) {
// 											fileName += ".xml";
// 										}

// 										// Create XML Blob
// 										const blob = new Blob([xmlContent], {
// 											type: "application/xml;charset=utf-8"
// 										});

// 										// Download
// 										const url = window.URL.createObjectURL(blob);
// 										const link = document.createElement("a");

// 										link.href = url;
// 										link.download = fileName;
// 										link.style.display = "none";

// 										document.body.appendChild(link);
// 										link.click();

// 										// Immediate clean up for this iteration (safe because loop waits)
// 										document.body.removeChild(link);
// 										window.URL.revokeObjectURL(url);

// 										// Success message
// 										if (item.alert_msg) {
// 											frappe.show_alert({
// 												message: __(item.alert_msg),
// 												indicator: "green"
// 											});
// 										}

// 										// Sleep for exactly 1 second before allowing the next loop item to download
// 										await sleep(1000);

// 									} catch (err) {
// 										console.error("XML download failed:", err);

// 										frappe.msgprint({
// 											title: __("Download Error"),
// 											message: __("Unable to download {0}.", [item.file_name || "XML file"]),
// 											indicator: "red"
// 										});
// 									}
// 								}
// 							} else {
// 								frappe.msgprint(__("No records compiled for the selected filters. File generation stopped."));
// 							}
// 						}
// 					});
// 				}else {
// 					frappe.msgprint({
// 						title: __('Verification Failed'),
// 						indicator: 'red',
// 						message: __('Invalid authorization code.')
// 					});
// 				}
// 			}, __('Verification Required'), __('Submit'));
//         });

// 		}
       
//     },
// 	filters: [
// 		{
// 			fieldname: "from_date",
// 			label: __("From Date"),
// 			fieldtype: "Date",
// 			default: frappe.datetime.month_start(),
// 			reqd: 1
// 		},
// 		{
// 			fieldname: "to_date",
// 			label: __("To Date"),
// 			fieldtype: "Date",
// 			default: frappe.datetime.month_end(),
// 			reqd: 1
// 		},
// 		{
// 			fieldname: "company",
// 			label: __("Company"),
// 			fieldtype: "Link",
// 			options: "Company",
// 			get_query: function () {
// 				return {
// 					filters: {
// 						"company_code": ["!=", ""]
// 					}
// 				};
// 			},
// 			reqd: 1
// 		},
// 		{
// 			fieldname: "entry_for",
// 			label: __("Entry For"),
// 			fieldtype: "Select",
// 			options: [
// 				"",
// 				"Doc Nego",
// 				"Doc Refund",
// 				"Doc Received",
// 				"Interest Payment",
// 				"CC Received",
// 				"LC Payment",
// 				"U LC Payment",
// 				"Import Loan",
// 				"Import Loan Payment",
// 				"CC Received",
// 				"Sales"
// 			],
// 			default: ""
// 		}
// 	]
// };


// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["Tally Entry"] = {
    onload: function(report) {
        // Only allow Administrator to generate Tally XMLs
        if (frappe.session.user === "Administrator") {
            report.page.add_inner_button(__("Generate Tally XML"), function() {
                frappe.query_reports["Tally Entry"].handle_xml_generation(report);
            });
        }
    },

    handle_xml_generation: function(report) {
        let filters = report.get_values();

        // 1. Filter Validation
        if (!filters.company || !filters.from_date || !filters.to_date|| !filters.entry_for) {
            frappe.msgprint(__("Please select Company, From Date, and To Date filters."));
            return;
        }

        // 2. Dynamically Prepare Prompt Fields
        let prompt_fields = [
            {
                label: __('Enter Authorization Code'),
                fieldname: 'auth_code',
                fieldtype: 'Password',
                reqd: 1
            }
        ];

        if (filters.entry_for === "CC Received") {
            prompt_fields.push({
                label: __('Received Ref No.'),
                fieldname: 'received_ref_no',
                fieldtype: 'Data',
                reqd: 1
            });
        }

        // 2. Security Prompt
        frappe.prompt(prompt_fields, function(values) {
            // 3. Match Verification
            if (values.auth_code && values.auth_code.toLowerCase() === filters.entry_for.trim().toLowerCase()) {
                frappe.msgprint(__("Code verified. Generating Tally XML..."));
                if (values.received_ref_no) {
                    let clean_ref = values.received_ref_no.trim();
                    
                    // 1. Update the local filters object key to 'ref_no' for the API call
                    filters.rec_ref_no = clean_ref;
                    console.log(filters);

                    
                    // 2. Update the frontend UI filter field so the user sees it in the filter bar
                    if (frappe.query_report && frappe.query_report.set_filter_value) {
                        frappe.query_report.set_filter_value('rec_ref_no', clean_ref);
                    }
                }
                frappe.query_reports["Tally Entry"].fetch_tally_data(filters);
            } else {
                frappe.msgprint({
                    title: __('Verification Failed'),
                    indicator: 'red',
                    message: __('Invalid authorization code.')
                });
            }
        }, __('Verification Required'), __('Submit'));
    },

    fetch_tally_data: function(filters) {
        frappe.call({
            method: "ssd_app.utils.tally_xml.create_tally_xml.create_tally_xml",
            args: { filters: filters },
            freeze: true,
            freeze_message: __("Generating Tally XML..."),
            callback: async function (r) {
                if (r.message && r.message.status === "success" && Array.isArray(r.message.data_context) && r.message.data_context.length > 0) {
                    await frappe.query_reports["Tally Entry"].download_xml_files(r.message.data_context);
                } else {
                    frappe.msgprint(__("No records compiled for the selected filters. File generation stopped."));
                }
            }
        });
    },

    download_xml_files: async function(data_context) {
        const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

        for (const item of data_context) {
            try {
                if (!item.data) continue;

                const xmlContent = typeof item.data === "string" ? item.data.trim() : String(item.data);
                if (!xmlContent) continue;

                // Sanitize file name
                let fileName = item.file_name || "tally_export";
                fileName = fileName.replace(/[<>:"/\\|?*\x00-\x1F]/g, "_");
                if (!fileName.toLowerCase().endsWith(".xml")) {
                    fileName += ".xml";
                }

                // Initialize Document Blob Download
                const blob = new Blob([xmlContent], { type: "application/xml;charset=utf-8" });
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement("a");

                link.href = url;
                link.download = fileName;
                link.style.display = "none";
                document.body.appendChild(link);
                
                link.click();

                // Clean memory instantly 
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);

                if (item.alert_msg) {
                    frappe.show_alert({ message: __(item.alert_msg), indicator: "green" });
                }

                // Await 1 second before forcing next item download browser cycle
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
                "Sales",
                "Doc Nego",
                "Doc Refund",
                "Doc Received",
                "Interest Payment",
                "CC Received",
                // "LC Payment",
                // "U LC Payment",
                // "Import Loan",
                // "Import Loan Payment"
            ],
            default: ""
        }
    ]
};
