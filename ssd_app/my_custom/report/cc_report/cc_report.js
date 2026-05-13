
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

        if (column.fieldname === "cc" && data.type === "rec") {

            return `
                <a href="#"
                    style="font-weight:600;"
                    onclick="show_cc_dialog('${data.name}'); return false;">
                    ${value || 0}
                </a>
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
                frappe.route_options = {
                    redirect_after_save: "CC Report"
                };


                frappe.set_route(
                    "Form",
                    "CC Received",
                    doc.name
                );
            });

        }
    });
}


window.view_cc_breakup_details = function(ref_no, customer) {
    frappe.call({
        method: "ssd_app.my_custom.doctype.cc_received.cc_received.get_ref_details",
        args: { ref_no: ref_no, customer:customer },
        callback: function(r) {
            if (!r.message || r.message.length === 0) {
                frappe.msgprint(__("No breakup details found for {0}", [ref_no]));
                return;
            }

            let rows = r.message.map(d => `
                <tr>
                    <td>${d.date}</td>
                    <td>${d.ref_no}</td>
                    <td style="text-align:right;">${format_currency(d.amount)}</td>
                    <td style="text-align:center;">
                        <a class="btn-edit-cc" data-name="${d.parent}" style="cursor:pointer;">
                            <svg class="icon icon-sm" style="stroke: var(--primary-color);">
                                <use href="#icon-edit"></use>
                            </svg>
                        </a>
                    </td>
                </tr>
            `).join("");

            let detail_dialog = new frappe.ui.Dialog({
                title: __("Breakup History: {0}", [ref_no]),
                fields: [{
                    fieldtype: "HTML",
                    fieldname: "history_html",
                    options: `
                        <table class="table table-bordered small">
                            <thead>
                                <tr class="text-muted">
                                    <th>Date</th>
                                    <th>Ref No</th>
                                    <th style="text-align:right;">Amount</th>
                                    <th style="text-align:center;">Action</th>
                                </tr>
                            </thead>
                            <tbody>${rows}</tbody>
                        </table>
                    `
                }]
            });

            /* --- MOVE THE LISTENER INSIDE HERE --- */
            detail_dialog.$wrapper.on("click", ".btn-edit-cc", function() {
                const docname = $(this).attr("data-name");

                frappe.route_options = {
                    "redirect_after_save": "CC Report"
                };

                detail_dialog.hide();
                frappe.set_route("Form", "CC Received", docname);
            });

            detail_dialog.show();
        }
    });
};
