// // Copyright (c) 2025, SSDolui and contributors
// // For license information, please see license.txt
// Load html2pdf only once
if (typeof html2pdf === "undefined") {
    const script = document.createElement("script");
    script.src = "https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js";
    script.defer = true;
    document.head.appendChild(script);
}


frappe.query_reports["CIF Sheet Table"] = {
    onload: function (report) {
        report.page.add_inner_button("Shipping Book Table", function (){
            frappe.set_route("query-report", "Shipping Book Table")
        })
        report.page.add_inner_button("Cost Sheet Table", function () {
            frappe.set_route("query-report", "Cost Sheet Table");
        });
        report.page.add_inner_button(__("Create New"), function () {
            // Set the flag in sessionStorage before navigating
            sessionStorage.setItem('return_to_after_save', 'CIF Sheet Table');
            frappe.new_doc("CIF Sheet");
        });

        report.refresh();

        frappe.call({
            method: "ssd_app.my_custom.report.cif_sheet_table.cif_sheet_table.get_years",
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

            let cost_button = "";

            if (!data.cost_id) {
                cost_button = `
                    <a href="#"
                        onclick="create_cost_sheet('${data.cif_id}'); return false;"
                        title="Create Cost Sheet">
                        <svg class="icon icon-sm">
                            <use href="#icon-upload"></use>
                        </svg>
                    </a>
                `;
            }

            return `
                <div style="display:flex; gap:12px; align-items:center;">

                    <!-- Edit -->
                    <a href="/app/cif-sheet/${data.cif_id}"
                        onclick="sessionStorage.setItem('return_to_after_save', 'CIF Sheet Table')"
                        title="Edit">
                        <svg class="icon icon-sm">
                            <use href="#icon-edit"></use>
                        </svg>
                    </a>

                    <!-- Search -->
                    <a href="#"
                        onclick="showCIFDetails('${data.cif_id}', '${data.inv_no}'); return false;"
                        title="View Details">
                        <svg class="icon icon-sm">
                            <use href="#icon-search"></use>
                        </svg>

                    </a>

                    ${cost_button}

                </div>
            `;
        }
       if (column.fieldname === "supplier" && value) {
            return `<div style="text-align:left;">${value}</div>`;
        }

        // Status column – 2 color pie (Received vs Outstanding)
        if (column.fieldname === "status" && value) {

            let color = "#f59e0b"; // default orange

            if (value === "Full Rec") {
                color = "#16a34a"; // green
            }
            else if (value === "Not Rec") {
                color = "#dc2626"; // red
            }

            return `
                <a href="#"
                    onclick="showDocFlow('${data.name}',  '${data.inv_no}'); return false;"
                    title="${value}"
                    style="display:inline-block; cursor:pointer;">

                    <div style="
                        width:10px;
                        height:10px;
                        border-radius:50%;
                        background:${color};
                    ">
                    </div>

                </a>
            `;
        }

        // Clickable inv_no with modal
        if (column.fieldname === "inv_no" && data && data.cif_id) {
            return `<a href="#" onclick="showCIFDetails('${data.cif_id}', '${data.inv_no}'); return false;">${data.inv_no}</a>`;
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


function create_cost_sheet(inv_no) {
    // frappe.return_to_page='CIF Sheet Table';
    sessionStorage.setItem(
        'return_to_after_save',
        'CIF Sheet Table'
    );

    frappe.new_doc("Cost Sheet");

    setTimeout(() => {
        cur_frm.set_value("inv_no", inv_no);
    }, 200);
}
