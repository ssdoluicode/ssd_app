// Copyright (c) 2026, SSDolui and contributors
// For license information, please see license.txt

function validate_inv_no(frm){
    if (!frm.doc.inv_no) return;
    frappe.db.get_value('Shipping Book', { inv_no: frm.doc.inv_no }, 'name')
    .then(r => {
        if (r && r.message && r.message.name && r.message.name !== frm.doc.name) {
            frappe.msgprint({
                title: __(`Duplicate Entry: ${frm.doc.inv_no}`),
                message: __('Invoice Number must be unique. This one already exists.'),
                indicator: 'red'
            });
            frm.set_value('inv_no', '');
        }
    });
}


function apply_payment_term_filter(frm) {

    // Filter Payment Term list
    frm.set_query("payment_term", function () {
        return {
            filters: [
                ["Payment Term", "term_type", "=", "Export"],
                ["Payment Term", "active", "=", 1]
            ]
        };
    });

    let pt = frm.doc.payment_term;
    if (!pt) return;

    frappe.db.get_value("Payment Term", pt, ["full_tt", "use_banking_line"])
        .then(r => {

            if (!r.message) return;

            let { full_tt, use_banking_line } = r.message;

            // Banking fields
            frm.set_df_property("bank", "reqd", use_banking_line ? 1 : 0);
            frm.set_df_property("term_days", "reqd", use_banking_line ? 1 : 0);

            // Document field logic
            
            if (full_tt == 1) {
                frm.set_value("document", 0);
                frm.set_df_property("document", "read_only", 1);
            } else {
                frm.set_df_property("document", "read_only", 0);
                if (frm.is_new()){
                    frm.set_value("document", frm.doc.invoice_amount);
                }
            }

            frm.refresh_field(["bank", "term_days", "document"]);

        });
}

function check_and_lock_fields(frm) {
    if (frm.is_new() || !frm.doc.name || !frm.doc.inv_no) return;
    frappe.call({
        method: "ssd_app.my_custom.doctype.shipping_book.shipping_book.check_related_docs",
        args: { inv_id: frm.doc.name }
    }).then(r => {
        if (r.message === true) {
            frm.set_df_property("invoice_amount", "read_only", 1);
            frm.set_df_property("document", "read_only", 1);
            frm.set_df_property("bank", "read_only", 1);
            frm.set_df_property("payment_term", "read_only", 1);
        }
    });
}


frappe.ui.form.on("Shipping Book", {
    onload(frm){
        // check_and_lock_fields(frm);
        apply_payment_term_filter(frm);
    },
	inv_no(frm) {
        validate_inv_no(frm);
    },
    invoice_amount(frm) {
        apply_payment_term_filter(frm);
    },
    payment_term(frm){
        apply_payment_term_filter(frm);

    }
});
