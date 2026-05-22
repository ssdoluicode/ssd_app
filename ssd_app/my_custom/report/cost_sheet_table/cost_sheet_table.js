if (typeof Chart === "undefined") {
    const chartScript = document.createElement("script");
    chartScript.src = "https://cdn.jsdelivr.net/npm/chart.js";
    chartScript.defer = true;
    document.head.appendChild(chartScript);
}

frappe.query_reports["Cost Sheet Table"] = {
	onload: function (report) {
        report.page.add_inner_button("CIF Sheet Table", function () {
            frappe.set_route("query-report", "CIF Sheet Table");
        });
        report.page.add_inner_button(__("Create New"), function () {
            // Set the flag in sessionStorage before navigating
            sessionStorage.setItem('return_to_after_save', 'Cost Sheet Table');
            frappe.new_doc("Cost Sheet");
        });
        frappe.call({
            method: "ssd_app.my_custom.report.cost_sheet_table.cost_sheet_table.get_years",
            callback: function (r) {
                if (r.message) {
                    let year_filter = report.get_filter("year");
                    let years = r.message;

                    // ✅ Set default as MAX year
                    year_filter.df.default = Math.max(...years.map(y => parseInt(y))).toString();

                    // ✅ Add "All" option at the beginning
                    years.unshift("All");

                    // ✅ Set options
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

        // 🔗 Clickable inv_no with modal
        if (column.fieldname === "inv_no" && data && data.cif_id) {
            return `<a href="#" onclick="showCostDetails('${data.cif_id}', '${data.inv_no}'); return false;">${data.inv_no}</a>`;
        }
        if (column.fieldname === "action" && value) {

            return `
                <div style="display:flex; gap:12px; align-items:center;">

                    <!-- Edit -->
                    <a href="/app/cost-sheet/${data.name}"
                        onclick="sessionStorage.setItem('return_to_after_save', 'Cost Sheet Table')"
                        title="Edit">
                        <svg class="icon icon-sm">
                            <use href="#icon-edit"></use>
                        </svg>
                    </a>

                    <!-- Search -->
                    <a href="#"
                        onclick="showCostDetails('${data.cif_id}', '${data.inv_no}'); return false;"
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
            default: 0,
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



