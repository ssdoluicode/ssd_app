function bankingLineBalance() {
    frappe.call({
        method: "ssd_app.my_custom.doctype.lc_open.lc_open.banking_line_balance",
        args: {},
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
                title: `Banking Line Balance`,
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

function importBanking(as_on) {
    columns_order = ["Cash Loan", "Imp Loan", "LC Open", "Usance LC"] 
    frappe.call({
        method: "ssd_app.my_custom.doctype.lc_open.lc_open.import_banking",
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
                title: `Import Banking Line`,
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

function usedBankingLine(as_on) {
    columns_order = ["LC", "LC at Sight", "DA", "DP", "Cash Loan", "Imp Loan", "LC Open", "Usance LC"] 
    frappe.call({
        method: "ssd_app.my_custom.doctype.doc_nego.doc_nego.used_banking_line",
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
                title: `Import Banking Line`,
                size: 'extra-large',
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

function bankingLine() {
    frappe.call({
        method: "ssd_app.my_custom.doctype.lc_open.lc_open.banking_line",
        args: {},
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



// 🧾 Modal Dialog to Show Document Flow
function showDocFlow(inv_name, inv_no) {
    frappe.call({
        method: "ssd_app.my_custom.report.document_receivable.document_receivable.get_doc_flow",
        args: { inv_name },
        callback: function (r) {
            if (r.message) {
                const d = new frappe.ui.Dialog({
                    title: `Document Flow for: ${inv_no}`,
                    size: 'extra-large',
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
                        method: "ssd_app.my_custom.report.document_receivable.document_receivable.get_doc_flow",
                        args: { inv_name },
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


function showCIFDetails(inv_name, inv_no) {
    frappe.call({
        method: "ssd_app.my_custom.doctype.cif_sheet.cif_sheet.render_cif_sheet_pdf",
        args: { inv_name },
        callback: function (r) {
            if (!r.message) return;

            const htmlContent = `
                <div id="cif-details-a4" style="
                    width: 20cm;
                    max-width: 100%;
                    min-height: 28.7cm;
                    padding: 0.3cm;
                    background: white;
                    font-size: 13px;
                    box-shadow: 0 0 8px rgba(0,0,0,0.2);"
                >${r.message}</div>
            `;

            const dialog = new frappe.ui.Dialog({
                title: `CIF Sheet: ${inv_no}`,
                size: 'large',
                primary_action_label: 'PDF',
                primary_action() {
                    window.open(
                        `/api/method/ssd_app.my_custom.doctype.cif_sheet.cif_sheet.render_cif_sheet_pdf?inv_name=${inv_name}&pdf=1`,
                        '_blank'
                    );
                },
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'details_html',
                        options: htmlContent
                    }
                ]
            });

            dialog.show();

            // ------------------------------------------
            // ⭐ Add custom buttons inside title bar
            // ------------------------------------------
            const $title_area = dialog.$wrapper.find('.modal-title');

            // Set the title area to a flex container to control button alignment
            $title_area.css({
                display: 'flex',
                'justify-content': 'flex-end',  // Align buttons to the right
                'gap': '8px',  // Optional: adds space between buttons
                'align-items': 'center'  // Vertically center the buttons if needed
            });

            // Cost Sheet Button (Right-aligned)
            const costBtn = $(`
                <button class="btn btn-sm btn-primary">
                    Cost Sheet
                </button>
            `);

            costBtn.on("click", function () {
                showCostDetails(inv_name, inv_no);
            });

            // Master Sheet Button (Right-aligned)
            const masterBtn = $(`
                <button class="btn btn-sm btn-primary">
                    Master Sheet
                </button>
            `);

            masterBtn.on("click", function () {
                showMasterDetails(inv_name, inv_no);
            });

            // Append both buttons to the title area (right side)
            $title_area.append(costBtn);
            $title_area.append(masterBtn);

        }
    });
}



function showCostDetails(inv_name, inv_no) {
    frappe.call({
        method: "ssd_app.my_custom.doctype.cost_sheet.cost_sheet.render_cost_sheet_pdf",
        args: { inv_name },
        callback: function (r) {
            if (!r.message) return;
            const htmlContent = `
                <div id="cost-details-a4" style="
                    width: 20cm;
                    max-width: 100%;
                    min-height: 28.7cm;
                    padding: 0.3cm;
                    background: white;
                    font-size: 13px;
                    box-shadow: 0 0 8px rgba(0,0,0,0.2);"
                >${r.message}</div>
            `;

            const dialog = new frappe.ui.Dialog({
                title: `Cost Sheet: ${inv_no}`,
                size: 'large',
                primary_action_label: 'PDF',
                primary_action() {
                    window.open(
                        `/api/method/ssd_app.my_custom.doctype.cost_sheet.cost_sheet.render_cost_sheet_pdf?cost_id=${inv_name}&pdf=1`,
                        '_blank'
                    );
                },
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'details_html',
                        options: htmlContent
                    }
                ]
            });

            dialog.show();
            // ------------------------------------------
            // ⭐ Add custom buttons inside title bar
            // ------------------------------------------
            const $title_area = dialog.$wrapper.find('.modal-title');

            // Set the title area to a flex container to control button alignment
            $title_area.css({
                display: 'flex',
                'justify-content': 'flex-end',  // Align buttons to the right
                'gap': '8px',  // Optional: adds space between buttons
                'align-items': 'center'  // Vertically center the buttons if needed
            });

            // Cost Sheet Button (Right-aligned)
            const costBtn = $(`
                <button class="btn btn-sm btn-primary">
                    CIF Sheet
                </button>
            `);

            costBtn.on("click", function () {
                showCIFDetails(inv_name, inv_no);
            });

            // Master Sheet Button (Right-aligned)
            const masterBtn = $(`
                <button class="btn btn-sm btn-primary">
                    Master Sheet
                </button>
            `);

            masterBtn.on("click", function () {
                showMasterDetails(inv_name, inv_no);
            });

            // Append both buttons to the title area (right side)
            $title_area.append(costBtn);
            $title_area.append(masterBtn);

        }
    });
} 

function showMasterDetails(inv_name, inv_no) {
    frappe.call({
        method: "ssd_app.my_custom.doctype.cif_sheet.cif_sheet.render_master_sheet_pdf",
        args: { inv_name },
        callback: function (r) {
            if (!r.message) return;
            const htmlContent = `
                <div id="cif-details-a4" style="
                    width: 20cm;
                    max-width: 100%;
                    min-height: 28.7cm;
                    padding: 0.3cm;
                    background: white;
                    font-size: 13px;
                    box-shadow: 0 0 8px rgba(0,0,0,0.2);"
                >${r.message}</div>
            `;

            const dialog = new frappe.ui.Dialog({
                title: `Master Sheet: ${inv_no}`,
                size: 'large',
                primary_action_label: 'PDF',
                primary_action() {
                    window.open(
                        `/api/method/ssd_app.my_custom.doctype.cif_sheet.cif_sheet.render_master_sheet_pdf?inv_name=${inv_name}&pdf=1`,
                        '_blank'
                    );
                },
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'details_html',
                        options: htmlContent
                    }
                ]
            });

            dialog.show();

            // ------------------------------------------
            // ⭐ Add custom buttons inside title bar
            // ------------------------------------------
            const $title_area = dialog.$wrapper.find('.modal-title');

            // Set the title area to a flex container to control button alignment
            $title_area.css({
                display: 'flex',
                'justify-content': 'flex-end',  // Align buttons to the right
                'gap': '8px',  // Optional: adds space between buttons
                'align-items': 'center'  // Vertically center the buttons if needed
            });

            // Cost Sheet Button (Right-aligned)
            const costBtn = $(`
                <button class="btn btn-sm btn-primary">
                    CIF Sheet
                </button>
            `);

            costBtn.on("click", function () {
                showCIFDetails(inv_name, inv_no);
            });

            // Master Sheet Button (Right-aligned)
            const masterBtn = $(`
                <button class="btn btn-sm btn-primary">
                    Cost Sheet
                </button>
            `);

            masterBtn.on("click", function () {
                showCostDetails(inv_name, inv_no);
            });

            // Append both buttons to the title area (right side)
            $title_area.append(costBtn);
            $title_area.append(masterBtn);
        }
    });
} 


function showImportBankingFlow(lc_no, inv_no, dc_name) {
    frappe.call({
        method: "ssd_app.my_custom.report.import_banking.import_banking.get_import_banking_flow",
        args: { lc_no, inv_no, dc_name },
        callback: function (r) {
            if (r.message) {
                const d = new frappe.ui.Dialog({
                    title: `Document Flow for: ${inv_no}`,
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
                        args: { lc_no, inv_no, dc_name },
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

