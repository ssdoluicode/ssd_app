// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

// 🧠 Fetch negotiation data based on selected inv_no
function get_supplier(frm) {
    if (!frm.doc.inv_no) return;

    if (frm.is_new() && !frappe.quick_entry) {
        frappe.call({
            method: "ssd_app.my_custom.doctype.import_loan.import_loan.get_supplier",
            args: { invoice_no: frm.doc.inv_no },
            callback: function (r) {
                const data = r.message;
                if (!data) return;

                frm.set_value({
                    supplier: data.supplier
                });
            }
        });
    }
}

function calculate_due_date(frm) {
    if (frm.doc.loan_date && frm.doc.term_days) {

        let loan_date = frappe.datetime.str_to_obj(frm.doc.loan_date);
        let due_date = frappe.datetime.add_days(loan_date, frm.doc.term_days);

        frm.set_value("due_date", frappe.datetime.obj_to_str(due_date));
    }
}

function calculate_term_days(frm) {
    if (frm.doc.loan_date && frm.doc.due_date) {

        let diff = frappe.datetime.get_diff(frm.doc.due_date, frm.doc.loan_date);
        frm.set_value("term_days", diff);
    }
}

function calculate_amount_usd(frm){
    if (frm.doc.loan_amount && frm.doc.ex_rate) {
        frm.set_value("loan_amount_usd",parseFloat((frm.doc.loan_amount / frm.doc.ex_rate).toFixed(2)));
    }

}

frappe.ui.form.on("Import Loan", {
    loan_date(frm) {
        calculate_due_date(frm);
        calculate_term_days(frm);
    },
    inv_no(frm){
        get_supplier(frm);
    },

    term_days(frm) {
        calculate_due_date(frm);
    },
    due_date(frm){
        calculate_term_days(frm);
    },
    loan_amount(frm){
        calculate_amount_usd(frm);
    },
    ex_rate(frm){
        calculate_amount_usd(frm);
    },

	after_save(frm) {
        // Redirect to your report page "Import Banking"
         window.location.href = "/app/query-report/Import Banking ";
    }
});
