
// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["Import Banking"] = {
    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        // if (column.fieldname === "lc_open" && data?.name && column.dc_name=="lc_open") {
        //     return `<a style="color:blue;"  href="#" onclick="showDocFlow('${data.name}', '${data.inv_no}'); return false;">${Number(data.document).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</a>`;
        // }
        if (column.fieldname === "due_date" && data?.due_date) {
            let style = "font-weight: bold;";
            let clickable = "";//

            if (!data.due_date_confirm) {
                style += " text-decoration-line: underline;";
                style += " text-decoration-style: double;";
                style += " text-decoration-color: red; cursor:pointer;";
                let doc_no = data.inv_no ? data.inv_no : data.lc_no; 
                clickable = `onclick="changeDueDate('${data.name}', '${data.dc_name}', '${data.due_date}', '${doc_no}'); return false;"`;
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

        if (column.fieldname === "bank" && data?.bank) {
            return `<a style="color:blue;"  href="#" onclick="showImportBankingFlow('${data.name}', '${data.dc_name}', '${data.supplier}', '${data.bank}'); return false;">${data.bank}</a>`;
        }
        return value;
    },

	onload: function (report) {
		// report.page.add_inner_button("New LC Open", function () {
        //     frappe.new_doc("LC Open");
        // });
        
        report.page.add_inner_button("Doc Receivable", function () {
            frappe.set_route("query-report", "Document Receivable");
        });

        // report.page.add_inner_button("Import Banking Used", function () {
        //     let filters = report.get_values();
        //     importBanking(filters.as_on);
        // });
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

		report.page.add_inner_button("New LC Open", function () {
			frappe.new_doc("LC Open", true);
		}, "New");
        report.page.add_inner_button("New Import Loan", function () {
			frappe.new_doc("Import Loan", true);
		}, "New");
        report.page.add_inner_button("New Usance LC", function () {
			frappe.new_doc("Usance LC", true);
		}, "New");

		report.page.add_inner_button("New Cash Loan", function () {
			frappe.new_doc("Cash Loan", true);
		}, "New");
	},

	"filters": [
		{
            fieldname: "based_on",
            label: "Based On",
            fieldtype: "Select",
            options: "All\nCurrent Position\nLC Open\nUsance LC\nImport Loan\nCash Loan",
            default: "Current Position",
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



function showImportBankingFlow(name,  dc_name, supplier_name, bank_name) {
    frappe.call({
        method: "ssd_app.my_custom.report.import_banking.import_banking.get_import_banking_flow",
        args: { name,  dc_name, supplier_name, bank_name },
        callback: function (r) {
            if (r.message) {
                const d = new frappe.ui.Dialog({
                    title: `Document Flow for: ${name}`,
                    size: 'large',
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'details_html',
                            options: `
                                <div id="cif-details-a4" style="box-shadow: 0 0 8px rgba(0,0,0,0.2);">
                                    ${r.message}
                                </div>`
                        }
                    ]
                });
                d.show();

                // Add refresh button with better styling
                const $header = $(d.$wrapper).find('.modal-header');
                const refreshBtn = $(`
                    <button 
                        type="button" 
                        class="btn btn-light btn-sm" 
                        title="Refresh"
                        style="
                            margin-left: auto; 
                            margin-right: 20px; 
                            display: flex; 
                            align-items: center; 
                            gap: 8px;
                            border: 1px solid #ddd;
                            padding: 4px 8px;
                            font-size: 13px;
                        ">
                        <span style="font-size: 14px;">🔄</span> Refresh
                    </button>
                `);

                refreshBtn.on('click', function(e) {
                    e.preventDefault();
                    frappe.call({
                        method: "ssd_app.my_custom.report.import_banking.import_banking.get_import_banking_flow",
                        args: { lc_no,  dc_name, supplier_name, bank_name },
                        callback: function (res) {
                            if (res.message) {
                                d.set_value('details_html', `
                                    <div id="cif-details-a4" style="box-shadow: 0 0 8px rgba(0,0,0,0.2);">
                                        ${res.message}
                                    </div>`);
                            }
                        }
                    });
                });

                // Insert before the close (X) button for better spacing
                $header.find('.modal-title').after(refreshBtn);
            }
        }
    });
}

window.changeDueDate = function(name, dc_name, current_due_date, inv_no) {

    // First, fetch the current note from DB
    name_dict= {"imp_l":"Import Loan", "u_lc":"Usance LC", "c_loan":"Cash Loan"}
    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: name_dict[dc_name],
            name: name
        },
        callback: function(r) {
            const current_note = r.message?.note || "";

            // Now open the dialog with note pre-filled
            let d = new frappe.ui.Dialog({
                title: `Update Bank Date ${name_dict[dc_name]} of: ${inv_no}`,
                fields: [
                    {
                        label: "Current Due Date",
                        fieldname: "current_date",
                        fieldtype: "Data",
                        read_only: 1,
                        default: current_due_date
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
                        method: "ssd_app.my_custom.doctype.doc_nego.doc_nego.update_import_due_date",
                        args: {
                            doctype_name: name_dict[dc_name],
                            docname: name,
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

