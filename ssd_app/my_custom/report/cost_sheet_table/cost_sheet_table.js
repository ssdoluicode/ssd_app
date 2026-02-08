if (typeof Chart === "undefined") {
    const chartScript = document.createElement("script");
    chartScript.src = "https://cdn.jsdelivr.net/npm/chart.js";
    chartScript.defer = true;
    document.head.appendChild(chartScript);
}

frappe.query_reports["Cost Sheet Table"] = {
	onload: function (report) {
        report.page.add_inner_button("Open Cost Sheet List", function () {
            frappe.set_route("List", "Cost Sheet");
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

        // // 🎯 Status column – 2 color pie (Received vs Outstanding)
        // if (column.fieldname ===  "status" && value) {

        //     const total = flt(data.document || 0);
        //     const received = flt(data.total_rec || 0);

        //     let percent = 0;
        //     if (total > 0) {
        //         percent = Math.min(100, Math.round((received / total) * 100));
        //     }

        //     return `
        //         <a href="#"
        //         onclick="showDocFlow('${data.name}'); return false;"
        //         title="Received ${percent}%"
        //         style="display:inline-block; cursor:pointer;">
        //             <div style="
        //                 width:14px;
        //                 height:14px;
        //                 border-radius:50%;
        //                 background: conic-gradient(
        //                     #16a34a ${percent}%,
        //                     #dc2626 ${percent}% 100%
        //                 );
        //             ">
        //             </div>
        //         </a>
        //     `;
        // }

        // 🔗 Clickable inv_no with modal
        if (column.fieldname === "inv_no" && data && data.cif_id) {
            return `<a href="#" onclick="showCostDetails('${data.cif_id}', '${data.inv_no}'); return false;">${data.inv_no}</a>`;
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
        }    
    ],
};
