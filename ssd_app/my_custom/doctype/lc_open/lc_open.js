// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

function calculate_usd(frm) {
    if (frm.doc.amount && frm.doc.ex_rate) {
        let usd = frm.doc.amount / frm.doc.ex_rate;
        frm.set_value('amount_usd', parseFloat(usd.toFixed(2)));
    }
}

frappe.ui.form.on("LC Open", {
    ex_rate: function(frm) {
        calculate_usd(frm);
    },
    amount: function(frm) {
        calculate_usd(frm);
    },
    after_save(frm) {
        // Redirect to your report page "Import Banking"
        frappe.set_route('query-report', 'Import Banking');
    }
});
