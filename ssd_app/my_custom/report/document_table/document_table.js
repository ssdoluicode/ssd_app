
// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["Document Table"] = {
	"filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(
                frappe.datetime.month_start(),
                -4
            ),
            "reqd": 1
        },

        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
		{
            "fieldname": "type",
            "label": __("Type"),
            "fieldtype": "Select",
            "options": ["All", "Nego", "Refund", "Received", "Interest"],
            "default": "All",
            "reqd": 1
        }
    ],
    

    onload: function(report) {
        report.page.add_inner_button(
            "New Interest Paid",
            function () {
                frappe.set_route("Form", "Interest Paid", "new-Interest Paid");
            }
        );
    },

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "document" && data?.shi_id) {
            return `<a style="color:blue;"  href="#" onclick="showDocFlow('${data.shi_id}', '${data.inv_no}'); return false;">${Number(data.document).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</a>`;
        }

        if (column.fieldname === "inv_no" && data?.cif_id) {
            return `<a style="color:blue;" href="#" onclick="showCIFDetails('${data.cif_id}', '${data.inv_no}'); return false;">${data.inv_no}</a>`;
        }
        if (column.fieldname === "bank_ch" && data?.shi_id) {
            return `<a style="color:blue;"  href="#" onclick="showFinanceCostDetails('${data.shi_id}', '${data.inv_no}'); return false;">${Number(data.bank_ch).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</a>`;
        }

        return value;
    }
};
	