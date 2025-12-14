frappe.query_reports["Document Receivable"] = {
    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "bank_due_date" && data?.bank_due_date) {
            let style = "font-weight: bold;";
            let clickable = "";//

            if (!data.due_date_confirm) {
                style += " text-decoration-line: underline;";
                style += " text-decoration-style: double;";
                style += " text-decoration-color: red; cursor:pointer;";
                clickable = `onclick="changeBankDueDate('${data.nego_name}', '${data.inv_no}', '${data.bank_due_date}'); return false;"`;
                if (data.days_to_due < 5) {
                    style += " color: red;";
                }
            } else {
        
                if (data.days_to_due < 5) {
                    style += " color: red;";
                }
            }

            // return `<span style="${style}">${value}</span>`;
            return `<span style="${style}" ${clickable}>${value}</span>`;
        }

        if (column.fieldname === "document" && data?.name) {
            return `<a style="color:blue;"  href="#" onclick="showDocFlow('${data.name}', '${data.inv_no}'); return false;">${Number(data.document).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</a>`;
        }
        if (column.fieldname === "inv_no" && data?.name) {
            return `<a style="color:blue;" href="#" onclick="showCIFDetails('${data.name}', '${data.inv_no}'); return false;">${data.inv_no}</a>`;
        }

        return value;
    },

    onload: function (report) {
        // for adjust width of serial no
        const style = document.createElement('style');
        style.textContent = `
            .dt-scrollable .dt-cell__content:first-child,
            .dt-scrollable .dt-header__cell:first-child {
                min-width: 50px !important;
            }
        `;
        document.head.appendChild(style);

        report.page.add_inner_button("Import Banking", function () {
            frappe.set_route("query-report", "Import Banking");
        });
        report.page.add_inner_button("Export Banking Used", function () {
            let filters = report.get_values();
            exportBankingLine(filters.as_on);
        });
         report.page.add_inner_button("Used Banking Line", function () {
            let filters = report.get_values();
            usedBankingLine(filters.as_on);
        });
        report.page.add_inner_button("Banking Line Balance", function () {
            bankingLineBalance();
        });
        report.page.add_inner_button("Banking Line", function () {
            bankingLine();
        });
    

       
    },

    filters: [
        {
            fieldname: "based_on",
            label: "Based On",
            fieldtype: "Select",
            options: "Receivable\nColl\nNego\nRefund\nAll",
            default: "Receivable",
            reqd: 1
        },
        {
            fieldname: "as_on",
            label: "As On",
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        }
    ]
};



function exportBankingLine(as_on) {
    columns_order=["LC", "LC at Sight","DA", "DP"]
    frappe.call({
        method: "ssd_app.my_custom.doctype.doc_nego.doc_nego.export_banking_line",
        args: {as_on, columns_order},
        callback: function (r) {
            if (!r.message) return;
            const htmlContent = `
                <div id="cif-details-a4" style="
                    width: 30cm;
                    max-width: 100%;
                    min-height: 5cm;
                    padding: 0.3cm;
                    background: white;
                    font-size: 13px;
                    box-shadow: 0 0 8px rgba(0,0,0,0.2);"
                >${r.message}</div>
            `;

            const dialog = new frappe.ui.Dialog({
                title: `Banking Line`,
                size: 'large',
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'details_html',
                        options: htmlContent
                    }
                ]
            });

            dialog.show();
        }
    });
} 


window.changeBankDueDate = function(nego_name, inv_no, current_date) {

    // First, fetch the current note from DB
    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Doc Nego",
            name: nego_name
        },
        callback: function(r) {
            const current_note = r.message?.note || "";

            // Now open the dialog with note pre-filled
            let d = new frappe.ui.Dialog({
                title: `Update Bank Due Date Inv No: ${inv_no}`,
                fields: [
                    {
                        label: "Current Due Date",
                        fieldname: "current_date",
                        fieldtype: "Data",
                        read_only: 1,
                        default: current_date
                    },
                    {
                        label: "New Due Date",
                        fieldname: "new_due_date",
                        fieldtype: "Date",
                        reqd: 1
                    },
                    {
                        label: "Due Date Confirm",
                        fieldname: "due_date_confirm",
                        fieldtype: "Check",
                        default: 1
                    },
                    {
                        label: "Note",
                        fieldname: "note",
                        fieldtype: "Data",
                        default: current_note
                    }
                ],
                primary_action_label: "Update",
                primary_action(values) {
                    frappe.call({
                        method: "ssd_app.my_custom.doctype.doc_nego.doc_nego.update_export_due_date",
                        args: {
                            docname: nego_name,
                            new_due_date: values.new_due_date,
                            due_date_confirm: values.due_date_confirm,
                            note: values.note
                        },
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.msgprint("Due Date updated successfully!");
                                d.hide();
                                // @ts-ignore
                                frappe.query_report.refresh();
                            }
                        }
                    });
                }
            });

            d.show();
        }
    });
};
