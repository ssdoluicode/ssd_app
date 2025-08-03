// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

function calculate_usd(frm) {
    if (frm.doc.amount && frm.doc.ex_rate) {
        let usd = frm.doc.amount / frm.doc.ex_rate;
        frm.set_value('amount_usd', parseFloat(usd.toFixed(2)));
    }
}

frappe.ui.form.on("LC Open", {
    onload: function(frm) {
        if (!frm.doc.lc_open_date) {
            frm.set_value('lc_open_date', frappe.datetime.get_today());
        }
    },
    ex_rate: function(frm) {
        calculate_usd(frm);
    },
    amount: function(frm) {
        calculate_usd(frm);
    },
    after_save: function (frm) {
        if (frappe.route_options && frappe.route_options.from_report) {
            frappe.set_route("query-report", frappe.route_options.from_report);
        }
    }
});
