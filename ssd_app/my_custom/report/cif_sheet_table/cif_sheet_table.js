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
        report.page.add_inner_button("Open CIF Sheet List", function () {
            frappe.set_route("List", "CIF Sheet");
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
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        // 🎯 Highlight status column
        if (column.fieldname === "status" && data && data.status) {
            let style = "font-weight: bold;";
            if (value === "Paid") {
                style+="color: green;";
            } else if (value === "Part") {
                style+="color: purple;";
            } else if (value === "Unpaid") {
                style+="color: red;";
            }
            return `<a style="${style}" href="#" onclick="showDocFlow('${data.name}', '${data.inv_no}'); return false;">${value}</a>`;
        }

        // 🔗 Clickable inv_no with modal
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
        }    
    ],
};



