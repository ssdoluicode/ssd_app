// // Copyright (c) 2025, SSDolui and contributors
// // For license information, please see license.txt
// Load html2pdf only once
if (typeof html2pdf === "undefined") {
    const script = document.createElement("script");
    script.src = "https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js";
    script.defer = true;
    document.head.appendChild(script);
}


frappe.query_reports["CC Received Table"] = {
    onload: function (report) {
        report.page.add_inner_button("CIF Sheet Table", function (){
            frappe.set_route("query-report", "CIF Sheet Table")
        })
        report.page.add_inner_button("Cost Sheet Table", function () {
            frappe.set_route("query-report", "Cost Sheet Table");
        });
        report.page.add_inner_button(__("Create New"), function () {
            // Set the flag in sessionStorage before navigating
            sessionStorage.setItem('return_to_after_save', 'CC Received Table');
            frappe.new_doc("CC Received");
        });

        report.refresh();

        frappe.call({
            method: "ssd_app.my_custom.report.cc_received_table.cc_received_table.get_years",
            callback: function (r) {
                if (r.message) {
                    let year_filter = report.get_filter("year");
                    let years = r.message;

                    // Set default as MAX year
                    year_filter.df.default = Math.max(...years.map(y => parseInt(y))).toString();

                    // Add "All" option at the beginning
                    years.unshift("All");

                    // Set options
                    year_filter.df.options = years;

                    // Refresh to apply default & options
                    year_filter.refresh();
                    year_filter.set_input(year_filter.df.default);
                }
            }
        });
    },
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

                // Action Column
        if (column.fieldname === "action" && value) {

            return `
                <div style="display:flex; gap:12px; align-items:center;">

                    <!-- Edit -->
                    <a href="/app/cc-received/${data.name}"
                        onclick="sessionStorage.setItem('return_to_after_save', 'CC Received Table')"
                        title="Edit">
                        <svg class="icon icon-sm">
                            <use href="#icon-edit"></use>
                        </svg>
                    </a>
					<!-- Search -->
                    <a href="#"
                        onclick="show_cc_dialog('${data.name}'); return false;"
                        title="View Details">
                        <svg class="icon icon-sm">
                            <use href="#icon-search"></use>
                        </svg>

                    </a>

                </div>
            `;
        }
		return value;
    },
	filters: [   
        {
            fieldname: "year",
            label: "Year",
            fieldtype: "Select",
            options: [],   // will be filled dynamically
            reqd: 0
        },
        {
            fieldname: "limit",
            label: __("Limit"),
            fieldtype: "Select",
            options: [
                { "value": 100, "label": __("100") },
                { "value": 500, "label": __("500") },
                { "value": 0, "label": __("All") } // Use 0 or "" to represent 'No Limit' in your query
            ],
            default: 100,
            reqd: 0
        },
        {
            fieldname: "quick_search",
            label: __("Quick Search"),
            fieldtype: "Data",
            on_change: function() {
                const report = frappe.query_report;
                const search_term = (this.get_value() || "").toLowerCase();
                
                if (!report || !report.datatable) return;

                const datatable = report.datatable;
                const all_rows = datatable.datamanager.getRows();

                if (!search_term) {
                    // Reset to show everything
                    datatable.rowmanager.showRows(all_rows.map((_, i) => i));
                } else {
                    // Find indices of rows that match
                    const matches = all_rows
                        .map((row, index) => {
                            // Check every cell in the row
                            const has_match = row.some(cell => {
                                const val = String(cell.content || "").toLowerCase();
                                return val.includes(search_term);
                            });
                            return has_match ? index : null;
                        })
                        .filter(idx => idx !== null);

                    datatable.rowmanager.showRows(matches);
                }

                // Essential: Update the display dimensions and refresh
                datatable.dimensions.recompute();
                datatable.refresh();
            }
        }
    ],
};


function show_cc_dialog(name) {

    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "CC Received",
            name: name
        },
        callback: function(r) {

            if (!r.message) {
                frappe.msgprint("No data found");
                return;
            }

            let doc = r.message;

            let child_rows = doc.cc_breakup || [];

            let rows = "";

            child_rows.forEach(d => {

                rows += `
                    <tr>
                        <td>${d.ref_no || ""}</td>

                        <td style="text-align:right;">
                            ${format_currency(d.amount || 0)}
                        </td>
                    </tr>
                `;
            });

            let dialog = new frappe.ui.Dialog({
                title: "CC Received Details",
                size: "large",
                fields: [
                    {
                        fieldtype: "HTML",
                        fieldname: "details_html"
                    }
                ]
            });

            dialog.fields_dict.details_html.$wrapper.html(`

                <div style="padding:10px;">

                    <div style="
                        display:grid;
                        grid-template-columns:150px 1fr;
                        gap:8px;
                        margin-bottom:15px;
                    ">

                        <div><b>Date</b></div>
                        <div>${frappe.datetime.str_to_user(doc.date || "")}</div>

                        <div><b>Amount (USD)</b></div>
                        <div>
                            ${format_currency(doc.amount_usd || 0)}
                        </div>

                        <div><b>Narration</b></div>
                        <div>${doc.note || ""}</div>

                    </div>

                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>Ref No</th>
                                <th style="text-align:right;">Amount</th>
                            </tr>
                        </thead>

                        <tbody>
                            ${rows || `
                                <tr>
                                    <td colspan="2" style="text-align:center;">
                                        No Child Records Found
                                    </td>
                                </tr>
                            `}
                        </tbody>
                    </table>

                </div>
            `);

            dialog.show();

            // Add Edit Button Right Side of Title Bar
            let $edit_btn = $(`
                <button class="btn btn-primary btn-sm">
                    Edit
                </button>
            `);

            dialog.$wrapper
                .find(".modal-header")
                .css("display", "flex");

            dialog.$wrapper
                .find(".modal-title")
                .after($edit_btn);

            $edit_btn.css({
                "margin-left": "Auto",
                "margin-right": "50px"
            });
            // Edit Button Action
            $edit_btn.on("click", function () {

                dialog.hide();
                // frappe.route_options = {
                //     redirect_after_save: "CC Report"
                // };
                sessionStorage.setItem(
                    'return_to_after_save',
                    'CC Received Table'
                );


                frappe.set_route(
                    "Form",
                    "CC Received",
                    doc.name
                );
            });

        }
    });
}

