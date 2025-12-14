// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

function get_supplier(frm) {
    if (!frm.doc.inv_no) return;

    if (frm.is_new() && !frappe.quick_entry) {
        frappe.call({
            method: "ssd_app.my_custom.doctype.usance_lc.usance_lc.get_supplier",
            args: { invoice_no: frm.doc.inv_no },
            callback: function (r) {
                const data = r.message;
                if (!data) return;

                frm.set_value({
                    supplier: data.supplier,
                    inv_date: data.inv_date
                });
            }
        });
    }
}

function calculate_amount_usd(frm){
    if (frm.doc.usance_lc_amount && frm.doc.ex_rate) {
        frm.set_value("usance_lc_amount_usd",parseFloat((frm.doc.usance_lc_amount / frm.doc.ex_rate).toFixed(2)));
    }
}

function calculate_due_date(frm) {
    if (frm.doc.inv_date && frm.doc.term_days) {

        let loan_date = frappe.datetime.str_to_obj(frm.doc.inv_date);
        let due_date = frappe.datetime.add_days(loan_date, frm.doc.term_days);

        frm.set_value("due_date", frappe.datetime.obj_to_str(due_date));
    }
}

frappe.ui.form.on("Usance LC", {
    inv_no(frm){
        get_supplier(frm);
        calculate_due_date(frm);
    },
    usance_lc_amount(frm){
        calculate_amount_usd(frm);
    },
    ex_rate(frm){
        calculate_amount_usd(frm);
    },
    inv_date(frm){
        calculate_due_date(frm);
    },
    term_days(frm){
        calculate_due_date(frm);
    },
	after_save: function(frm) {
        // Redirect to the report page after save
        window.location.href = "/app/query-report/Import Banking";
    }
});
