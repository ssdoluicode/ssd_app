// Copyright (c) 2026, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["Product Costing"] = {
	formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "inv_no" && data?.cif_id) {
            return `<a style="color:blue;" href="#" onclick="showCIFDetails('${data.cif_id}', '${data.inv_no}'); return false;">${data.inv_no}</a>`;
        }
        
        return value;
    },
    get_datatable_options(options) {
        options.freezeColumns = 2;   // Freeze first 2 columns
        return options;
    },



    onload: function (report) {

        report.page.add_inner_button("CIF Sheet Table", function () {
            frappe.set_route("query-report", "CIF Sheet Table");
        });
        report.page.add_inner_button("Cost Sheet Table", function () {
            frappe.set_route("query-report", "Cost Sheet Table");
        });
		frappe.call({
            method: "ssd_app.my_custom.report.cif_sheet_table.cif_sheet_table.get_years",
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

    filters: [
        {
            fieldname: "year",
            label: "Year",
            fieldtype: "Select",
            options: [],   // will be filled dynamically
            reqd: 0
        }
    ]


};
