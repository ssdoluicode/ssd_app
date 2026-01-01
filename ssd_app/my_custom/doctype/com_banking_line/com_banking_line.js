// Copyright (c) 2026, SSDolui and contributors
// For license information, please see license.txt

function banking_line_filter(frm) {
    frm.set_query("payment_term", () => ({
        query: "ssd_app.my_custom.doctype.com_banking_line.com_banking_line.banking_line_filter"
    }));
}

frappe.ui.form.on("Com Banking Line", {
	refresh(frm) {

	},
});
