// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["CC Statement"] = {
    onload: function(report) {
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
    },
	"filters": [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 1
        },
		{
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer",
            // default: "cus-0003",
            reqd: 1
        }

	],
	formatter: function (value, row, column, data, default_formatter) {
        // Get the default formatted value first
        value = default_formatter(value, row, column, data);

        // 🔑 Check if this row has note = "total"
        if (data && data.note && data.note.toLowerCase() === "total") {
            value = `<b>${value}</b>`;  // ✅ Bold entire row
        }
        if (data && data.note && data.note.toLowerCase() === "opening") {
            value = `<b>${value}</b>`;  // ✅ Bold entire row
        }
        if (column.fieldname === "inv_no" && data && data.name) {
            return `<a href="#" onclick="showCIFDetails('${data.name}', '${data.inv_no}'); return false;">${data.inv_no}</a>`;
        }
         return value;
    }
};
