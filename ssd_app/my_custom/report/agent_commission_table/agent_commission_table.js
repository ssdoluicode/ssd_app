// Copyright (c) 2026, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["Agent Commission Table"] = {
	onload: function (report) {
        report.set_filter_value("status", "Payable");
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

        // 🔗 Clickable inv_no with modal
        if (column.fieldname === "inv_no" && data && data.cif_id) {
            return `<a href="#" onclick="showCostDetails('${data.cif_id}', '${data.inv_no}'); return false;">${data.inv_no}</a>`;
        }

        if (column.fieldname === "comm_status" && data) {

            const commission = flt(data.commission || 0);
            const comm_paid = flt(data.comm_paid || 0);
            const document = flt(data.document || 0);
            const doc_rec = flt(data.doc_rec || 0);
            if (commission === 0) {
                return "";
            }

            let label = "";
            let color = "";
            let icon = "";
            let title = "";

            // ✅ PAID
            if (comm_paid === commission) {
                label = "Paid";
                color = "#16a34a";        // green
                icon = "check-circle";
                title = "Commission fully paid";

            // 🟡 CAN PAY
            } else if (comm_paid === 0 && document === doc_rec) {
                label = "Can Pay";
                color = "#f59e0b";
                icon = "circle";
                title = "Documents received, payment allowed";
            
            // 🟡 CAN PAY
            } else if (0<comm_paid<commission  && document === doc_rec) {
                label = "Partly Paid";
                color = "#f59e0b";
                icon = "circle";
                title = `Partly (paid ${comm_paid})`;


            // 🔴 HOLD
            } else if (comm_paid === 0 && document > doc_rec) {
                label = "Hold";
                color = "#dc2626";        // red
                icon = "ban";
                title = "Documents pending, commission on hold";

            } else {
                return "-";
            }

            return `
                <span title="${title}"
                    style="
                        display:inline-flex;
                        align-items:center;
                        gap:6px;
                        font-weight:600;
                        color:${color};
                    ">
                    <i class="fa fa-${icon}"></i>
                    ${label}
                </span>
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
        } ,
        {
            fieldname: "status",
            label: "Status",
            fieldtype: "Select",
            options: "\nAll\nPaid\nPayable\nCan Pay\nHold",
        } ,
        {
            fieldname: "as_on",
            label: "As On",
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
        }  
    ],
    
};
