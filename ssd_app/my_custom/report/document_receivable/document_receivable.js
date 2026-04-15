// frappe.query_reports["Document Receivable"] = {
//     formatter: function (value, row, column, data, default_formatter) {
//         value = default_formatter(value, row, column, data);

//         if (column.fieldname === "bank_due_date" && data?.bank_due_date) {
//             let style = "font-weight: bold;";
//             let clickable = "";//

//             if (!data.due_date_confirm) {
//                 style += " text-decoration-line: underline;";
//                 style += " text-decoration-style: double;";
//                 style += " text-decoration-color: red; cursor:pointer;";
//                 clickable = `onclick="changeBankDueDate('${data.nego_name}', '${data.invoice_no}', '${data.bank_due_date}'); return false;"`;
//                 if (data.days_to_due < 5) {
//                     style += " color: red;";
//                 }
//             } else {
        
//                 if (data.days_to_due < 5) {
//                     style += " color: red;";
//                 }
//             }

//             // return `<span style="${style}">${value}</span>`;
//             return `<span style="${style}" ${clickable}>${value}</span>`;
//         }

//         if (column.fieldname === "document" && data?.name) {
//             return `<a style="color:blue;"  href="#" onclick="showDocFlow('${data.name}', '${data.inv_no}'); return false;">${Number(data.document).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</a>`;
//         }
//         if (column.fieldname === "inv_no" && data?.cif_id) {
//             return `<a style="color:blue;" href="#" onclick="showCIFDetails('${data.cif_id}', '${data.inv_no}'); return false;">${data.inv_no}</a>`;
//         }

//         return value;
//     },

//     onload: function (report) {
//         // for adjust width of serial no
//         // const style = document.createElement('style');
//         // style.textContent = `
//         //     .dt-scrollable .dt-cell__content:first-child,
//         //     .dt-scrollable .dt-header__cell:first-child {
//         //         min-width: 50px !important;
//         //     }
//         // `;
//         // document.head.appendChild(style);

//         frappe.call({
//             method: "frappe.client.get_list",
//             args: {
//                 doctype: "Payment Term",
//                 fields: ["name"],
//                 filters: {
//                     term_type: "Export",
//                     use_banking_line: 1
//                 }
//             },
//             callback: function(r) {
//                 if (r.message) {
//                     let all_values = r.message.map(d => d.name);

//                     // ✅ set all values as selected
//                     report.set_filter_value("p_term", all_values);
//                 }
//             }
//         });
//         // let all_values = r.message.map(d => d.name);
//         // report.set_filter_value("p_term", all_values);

//         report.page.add_inner_button("Import Banking", function () {
//             frappe.set_route("query-report", "Import Banking");
//         });
//          report.page.add_inner_button("Used Banking Line", function () {
//             let filters = report.get_values();
//             usedBankingLine(filters.as_on);
//         });
//         report.page.add_inner_button("Banking Line Balance", function () {
//             bankingLineBalance();
//         });
//         report.page.add_inner_button("Banking Line", function () {
//             bankingLine();
//         });
//     },

//     filters: [
//         {
//             fieldname: "based_on",
//             label: "Based On",
//             fieldtype: "Select",
//             options: "Receivable\nColl\nNego\nRefund\nAll",
//             default: "Receivable",
//             reqd: 1
//         },
//         {
//             fieldname: "as_on",
//             label: "As On",
//             fieldtype: "Date",
//             default: frappe.datetime.get_today(),
//             reqd: 1
//         },
//         {
//             fieldname: "p_term",
//             label: "P Term",
//             fieldtype: "MultiSelectList",
//             options: "Payment Term",
//             get_data: function(txt) {
//                 return frappe.db.get_link_options("Payment Term", txt, {
//                     term_type: "Export",
//                     use_banking_line: 1
//                 });
//             }
//         }
//     ]
// };



// function exportBankingLine(as_on) {
//     columns_order=["LC", "LC at Sight","DA", "DP"]
//     frappe.call({
//         method: "ssd_app.my_custom.doctype.doc_nego.doc_nego.export_banking_line",
//         args: {as_on, columns_order},
//         callback: function (r) {
//             if (!r.message) return;
//             const htmlContent = `
//                 <div id="cif-details-a4" style="
//                     width: 30cm;
//                     max-width: 100%;
//                     min-height: 5cm;
//                     padding: 0.3cm;
//                     background: white;
//                     font-size: 13px;
//                     box-shadow: 0 0 8px rgba(0,0,0,0.2);"
//                 >${r.message}</div>
//             `;

//             const dialog = new frappe.ui.Dialog({
//                 title: `Banking Line`,
//                 size: 'large',
//                 fields: [
//                     {
//                         fieldtype: 'HTML',
//                         fieldname: 'details_html',
//                         options: htmlContent
//                     }
//                 ]
//             });

//             dialog.show();
//         }
//     });
// } 


// window.changeBankDueDate = function(nego_name, invoice_no, current_date) {

//     // First, fetch the current note from DB
//     frappe.call({
//         method: "frappe.client.get",
//         args: {
//             doctype: "Doc Nego",
//             name: nego_name
//         },
//         callback: function(r) {
//             const current_note = r.message?.note || "";

//             // Now open the dialog with note pre-filled
//             let d = new frappe.ui.Dialog({
//                 title: `Update Bank Due Date Inv No: ${invoice_no}`,
//                 fields: [
//                     {
//                         label: "Current Due Date",
//                         fieldname: "current_date",
//                         fieldtype: "Data",
//                         read_only: 1,
//                         default: current_date
//                     },
//                     {
//                         label: "New Due Date",
//                         fieldname: "new_due_date",
//                         fieldtype: "Date",
//                         reqd: 1
//                     },
//                     {
//                         label: "Due Date Confirm",
//                         fieldname: "due_date_confirm",
//                         fieldtype: "Check",
//                         default: 1
//                     },
//                     {
//                         label: "Note",
//                         fieldname: "note",
//                         fieldtype: "Data",
//                         default: current_note
//                     }
//                 ],
//                 primary_action_label: "Update",
//                 primary_action(values) {
//                     frappe.call({
//                         method: "ssd_app.my_custom.doctype.doc_nego.doc_nego.update_export_due_date",
//                         args: {
//                             docname: nego_name,
//                             new_due_date: values.new_due_date,
//                             due_date_confirm: values.due_date_confirm,
//                             note: values.note
//                         },
//                         callback: function(r) {
//                             if (!r.exc) {
//                                 frappe.msgprint("Due Date updated successfully!");
//                                 d.hide();
//                                 // @ts-ignore
//                                 frappe.query_report.refresh();
//                             }
//                         }
//                     });
//                 }
//             });
//             d.show();
//         }
//     });
// };



frappe.query_reports["Document Receivable"] = {
    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (!data) return value;

        const { fieldname } = column;

        // Handle Bank Due Date
        if (fieldname === "bank_due_date" && data.bank_due_date) {
            let styles = ["font-weight: bold"];
            let attributes = "";

            if (!data.due_date_confirm) {
                styles.push("text-decoration: underline double red", "cursor: pointer");
                attributes = `onclick="changeBankDueDate('${data.nego_name}', '${data.inv_no}', '${data.bank_due_date}'); return false;"`;
            }

            if (data.days_to_due < 5) {
                styles.push("color: red");
            }

            return `<span style="${styles.join(';')}" ${attributes}>${value}</span>`;
        }
        // if (column.fieldtype === "Date" && value) {
        //     return frappe.datetime.str_to_user(value);  
        // }

        // Handle Document Link
        if (fieldname === "document" && data.name) {
            const formattedNum = Number(data.document).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            return `<a style="color:blue;" href="#" onclick="showDocFlow('${data.name}', '${data.inv_no}'); return false;">${formattedNum}</a>`;
        }

        // Handle Invoice Link
        if (fieldname === "inv_no" && data.cif_id) {
            return `<a style="color:blue;" href="#" onclick="showCIFDetails('${data.cif_id}', '${data.inv_no}'); return false;">${data.inv_no}</a>`;
        }

        return value;
    },

    onload: function (report) {
        // Auto-select Export Payment Terms
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Payment Term",
                filters: { term_type: "Export", use_banking_line: 1 },
                fields: ["name"]
            },
            callback: (r) => {
                if (r.message) {
                    report.set_filter_value("p_term", r.message.map(d => d.name));
                }
            }
        });

        // Add Custom Buttons
        report.page.add_inner_button(__("Import Banking"), () => frappe.set_route("query-report", "Import Banking"));
        
        report.page.add_inner_button(__("Used Banking Line"), () => {
            const { as_on } = report.get_values();
            usedBankingLine(as_on);
        });

        report.page.add_inner_button(__("Banking Line Balance"), () => bankingLineBalance());
        
        report.page.add_inner_button(__("Banking Line"), () => bankingLine());
    },

    filters: [
        {
            fieldname: "based_on",
            label: __("Based On"),
            fieldtype: "Select",
            options: ["Receivable", "Coll", "Nego", "Refund", "All"],
            default: "Receivable",
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
            fieldname: "p_term",
            label: __("P Term"),
            fieldtype: "MultiSelectList",
            options: "Payment Term",
            get_data: (txt) => frappe.db.get_link_options("Payment Term", txt, {
                term_type: "Export",
                use_banking_line: 1
            })
        }
    ]
};

/**
 * Optimized Global Functions
 */

window.changeBankDueDate = function(nego_name, invoice_no, current_date) {
    // Faster fetch: only get the note field instead of the whole document
    frappe.db.get_value("Doc Nego", nego_name, "note", (r) => {
        const current_note = r?.note || "";

        const d = new frappe.ui.Dialog({
            title: `Update Bank Due Date: ${invoice_no}`,
            fields: [
                { label: "Current Due Date", fieldname: "current_date", fieldtype: "Data", read_only: 1, default: current_date },
                { label: "New Due Date", fieldname: "new_due_date", fieldtype: "Date", reqd: 1 },
                { label: "Due Date Confirm", fieldname: "due_date_confirm", fieldtype: "Check", default: 1 },
                { label: "Note", fieldname: "note", fieldtype: "Small Text", default: current_note }
            ],
            primary_action_label: __("Update"),
            primary_action(values) {
                frappe.call({
                    method: "ssd_app.my_custom.doctype.doc_nego.doc_nego.update_export_due_date",
                    args: {
                        docname: nego_name,
                        new_due_date: values.new_due_date,
                        due_date_confirm: values.due_date_confirm,
                        note: values.note
                    },
                    callback: (r) => {
                        if (!r.exc) {
                            frappe.show_alert({ message: __("Due Date updated"), indicator: 'green' });
                            d.hide();
                            frappe.query_report.refresh();
                        }
                    }
                });
            }
        });
        d.show();
    });
};

function exportBankingLine(as_on) {
    frappe.call({
        method: "ssd_app.my_custom.doctype.doc_nego.doc_nego.export_banking_line",
        args: { as_on, columns_order: ["LC", "LC at Sight", "DA", "DP"] },
        callback: (r) => {
            if (!r.message) return;
            
            const dialog = new frappe.ui.Dialog({
                title: __("Banking Line"),
                size: 'large',
                fields: [{
                    fieldtype: 'HTML',
                    fieldname: 'details_html',
                    options: `<div style="width: 100%; min-height: 5cm; padding: 10px; background: white; font-size: 13px; box-shadow: var(--shadow-sm);">${r.message}</div>`
                }]
            });
            dialog.show();
        }
    });
}