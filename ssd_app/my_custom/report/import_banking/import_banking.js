
// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.query_reports["Import Banking"] = {
    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        // if (column.fieldname === "lc_open" && data?.name && column.dc_name=="lc_open") {
        //     return `<a style="color:blue;"  href="#" onclick="showDocFlow('${data.name}', '${data.inv_no}'); return false;">${Number(data.document).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</a>`;
        // }
        if (column.fieldname === "bank" && data?.bank) {
            return `<a style="color:blue;"  href="#" onclick="showImportBankingFlow('${data.lc_no}', '${data.inv_no}', '${data.dc_name}'); return false;">${data.bank}</a>`;
        }
        

        return value;
    },

	onload: function (report) {
		// report.page.add_inner_button("New LC Open", function () {
        //     frappe.new_doc("LC Open");
        // });
		report.page.add_inner_button("New LC Open", function () {
			frappe.new_doc("LC Open", true);
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





function showImportBankingFlow(lc_no, inv_no, dc_name) {
    frappe.call({
        method: "ssd_app.my_custom.report.import_banking.import_banking.get_import_banking_flow",
        args: { lc_no, inv_no, dc_name },
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
