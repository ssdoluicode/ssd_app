
frappe.query_reports["CC Report"] = {

    onload(report) {
        this.add_buttons(report);
        this.set_default_from_date(report);
        this.override_refresh(report);
    },

    formatter(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        // 🔗 Clickable Invoice No
        if (column.fieldname === "inv_no" && data?.name) {
            return `
                <a href="#" data-name="${data.name}" data-inv="${data.inv_no}"
                   class="cif-link">${data.inv_no}</a>
            `;
        }

        // 🔹 Bold Opening rows
        if (data?.dev_note?.toLowerCase() === "opening") {
            value = `<b>${value}</b>`;
        }

        return value;
    },

    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 1
        },
        {
            fieldname: "as_on",
            label: __("As On"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer",
            reqd: 1
        }
    ],

    /* -------------------------
       Helper Methods
    ------------------------- */

    add_buttons(report) {
        report.page.add_inner_button(__("Balance Break"), () => {
            const { customer, as_on } = report.get_values();

            if (!customer || !as_on) {
                frappe.msgprint(__("Please select a Customer & Date first."));
                return;
            }

            cc_balance_breakup(customer, as_on);
        });

        report.page.add_inner_button(__("Go to CC Balance"), () => {
            frappe.set_route("query-report", "CC Balance");
        });
    },

    set_default_from_date(report) {
        frappe.call({
            method: "ssd_app.my_custom.report.dynamic_sales_report.dynamic_sales_report.get_first_jan_of_max_year",
            callback(r) {
                if (!r.message) return;

                const filter = report.get_filter("from_date");
                filter.df.default = r.message;
                filter.set_input(r.message);
            }
        });
    },

    override_refresh(report) {
        const original = report.refresh;

        report.refresh = function () {
            original.apply(this, arguments);

            setTimeout(() => {
                if (!report.datatable) return;

                report.datatable.options.disableSorting = true;
                $(report.page.wrapper)
                    .find(".dt-header .dt-cell")
                    .css("pointer-events", "none");
            }, 200);
        };
    }
};


/* =========================
   CC Balance Breakup Modal
========================= */

function cc_balance_breakup(customer, as_on) {
    frappe.call({
        method: "ssd_app.my_custom.doctype.cc_received.cc_received.cc_balance_breakup",
        args: { customer, as_on },
        callback(r) {
            if (!r.message) return;

            new frappe.ui.Dialog({
                title: __("CC Balance Breakup of: {0}", [customer]),
                size: "small",
                fields: [{
                    fieldtype: "HTML",
                    fieldname: "details_html",
                    options: render_cc_html(r.message)
                }]
            }).show();
        }
    });
}


/* =========================
   HTML Renderer
========================= */

function render_cc_html(content) {
    return `
        <div style="
            width: 20cm;
            max-width: 100%;
            min-height: 5cm;
            padding: 0.3cm;
            background: #fff;
            font-size: 13px;
            box-shadow: 0 0 8px rgba(0,0,0,.2);
        ">
            ${content}
        </div>
    `;
}


/* =========================
   CIF Click Handler (Delegated)
========================= */

$(document).on("click", ".cif-link", function (e) {
    e.preventDefault();
    showCIFDetails($(this).data("name"), $(this).data("inv"));
});

