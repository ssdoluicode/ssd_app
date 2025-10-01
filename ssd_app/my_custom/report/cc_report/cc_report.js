// // // Copyright (c) 2025, SSDolui
// // // For license information, please see license.txt

frappe.query_reports["CC Report"] = {


    onload: function (report) {
        report.page.add_inner_button("Balance Break", function () {
            // Fetch current filter values
            let filters = report.get_values();
            if (filters.customer && filters.as_on) {
                 ccBalanceBreakup(filters.customer, filters.as_on);
            } else {
                frappe.msgprint(__("Please select a Customer & Date first."));
            }
        });
        frappe.call({
            method: "ssd_app.my_custom.report.dynamic_sales_report.dynamic_sales_report.get_first_jan_of_max_year",
            callback: function(r) {
                if (r.message) {
                    const f = report.get_filter("from_date");
                    f.df.default = r.message;
                    f.set_input(r.message);
                }
            }
        });
        report.page.add_inner_button("Go to CC Balance", function () {
            frappe.set_route('query-report', 'CC Balance');
        });
        report.refresh = (function(orig) {
            return function() {
                orig.apply(this, arguments);
                setTimeout(() => {
                    if (report.datatable) {
                        report.datatable.options.disableSorting = true;
                        // also remove cursor pointer from headers
                        $(report.page.wrapper).find(".dt-header .dt-cell").css("pointer-events", "none");
                    }
                }, 200);
            };
        })(report.refresh);
    },
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
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 1
        },
        {
            "fieldname": "as_on",
            "label": __("As On"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer",
            // "default": "cus-0003",
            "reqd": 1
        }
    ]
};


function ccBalanceBreakup(cus_id, as_on) {
    frappe.call({
        method: "ssd_app.my_custom.doctype.cc_received.cc_received.cc_balance_breakup",
        args: { cus_id, as_on },
        callback: function (r) {
            if (!r.message) return;
            const htmlContent = `
                <div id="cif-details-a4" style="
                    width: 20cm;
                    max-width: 100%;
                    min-height: 5cm;
                    padding: 0.3cm;
                    background: white;
                    font-size: 13px;
                    box-shadow: 0 0 8px rgba(0,0,0,0.2);"
                >${r.message}</div>
            `;

            const dialog = new frappe.ui.Dialog({
                title: `CC Balabce Breakup of: ${cus_id}`,
                size: 'small',
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'details_html',
                        options: htmlContent
                    }
                ]
            });

            dialog.show();
        }
    });
} 

// frappe.query_reports["CC Report"] = {
//     onload: function (report) {
//         // Disable sorting after table renders
//         report.refresh = (function(orig) {
//             return function() {
//                 orig.apply(this, arguments);
//                 setTimeout(() => {
//                     if (report.datatable) {
//                         report.datatable.options.disableSorting = true;
//                         // also remove cursor pointer from headers
//                         $(report.page.wrapper).find(".dt-header .dt-cell").css("pointer-events", "none");
//                     }
//                 }, 200);
//             };
//         })(report.refresh);

//         // your buttons…
//         report.page.add_inner_button("Balance Break", function () {
//             let filters = report.get_values();
//             if (filters.customer && filters.as_on) {
//                 ccBalanceBreakup(filters.customer, filters.as_on);
//             } else {
//                 frappe.msgprint(__("Please select a Customer & Date first."));
//             }
//         });

//         report.page.add_inner_button("Go to CC Balance", function () {
//             frappe.set_route('query-report', 'CC Balance');
//         });
//     },

//     filters: [
//         {
//             "fieldname": "as_on",
//             "label": __("As On"),
//             "fieldtype": "Date",
//             "default": frappe.datetime.get_today(),
//             "reqd": 1
//         },
//         {
//             "fieldname": "customer",
//             "label": __("Customer"),
//             "fieldtype": "Link",
//             "options": "Customer",
//             "reqd": 1
//         }
//     ]
// };


// frappe.query_reports["CC Report"] = {
//     onload: function (report) {
//         // Disable sorting after table renders
//         report.refresh = (function(orig) {
//             return function() {
//                 orig.apply(this, arguments);
//                 setTimeout(() => {
//                     if (report.datatable) {
//                         report.datatable.options.disableSorting = true;
//                         // also remove cursor pointer from headers
//                         $(report.page.wrapper).find(".dt-header .dt-cell").css("pointer-events", "none");
//                     }
//                 }, 200);
//             };
//         })(report.refresh);

//         // your buttons…
//         report.page.add_inner_button("Balance Break", function () {
//             let filters = report.get_values();
//             if (filters.customer && filters.as_on) {
//                 ccBalanceBreakup(filters.customer, filters.as_on);
//             } else {
//                 frappe.msgprint(__("Please select a Customer & Date first."));
//             }
//         });

//         report.page.add_inner_button("Go to CC Balance", function () {
//             frappe.set_route('query-report', 'CC Balance');
//         });
//     },

//     filters: [
//         {
//             "fieldname": "as_on",
//             "label": __("As On"),
//             "fieldtype": "Date",
//             "default": frappe.datetime.get_today(),
//             "reqd": 1
//         },
//         {
//             "fieldname": "customer",
//             "label": __("Customer"),
//             "fieldtype": "Link",
//             "options": "Customer",
//             "reqd": 1
//         }
//     ]
// };
