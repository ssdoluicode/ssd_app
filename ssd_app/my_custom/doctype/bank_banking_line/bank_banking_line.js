// Copyright (c) 2026, SSDolui and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bank Banking Line", {

    refresh(frm) {
        toggle_banking_line(frm);
    },

    no_limit(frm) {
        toggle_banking_line(frm);
    }

});

function toggle_banking_line(frm) {
    if (frm.doc.no_limit) {
        frm.set_df_property("banking_line", "hidden", 1);
    } else {
        frm.set_df_property("banking_line", "hidden", 0);
    }
}
