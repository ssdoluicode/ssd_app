// // Copyright (c) 2026, SSDolui and contributors
// // For license information, please see license.txt


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
    frm.set_query("payment_term", function () {
        return {
            filters: [
                // Condition 1: full_tt based on document value
                ["Payment Term", "full_tt", "=", frm.doc.document > 0 ? 0 : 1],
                
                // Condition 2: term_type must be "Export"
                ["Payment Term", "term_type", "=", "Export"],
                
                // Condition 3: active must be 1 (Checked)
                ["Payment Term", "active", "=", 1]
            ]
        };
    });
}

function check_and_lock_fields(frm) {
    if (frm.is_new() || !frm.doc.name || !frm.doc.inv_no) return;
    frappe.call({
        method: "ssd_app.my_custom.doctype.shipping_book.shipping_book.check_related_docs",
        args: { inv_id: frm.doc.name }
    }).then(r => {
        if (r.message === true) {
            frm.set_df_property("document", "read_only", 1);
            frm.set_df_property("bank", "read_only", 1);
            frm.set_df_property("payment_term", "read_only", 1);
        }
    });
}

function toggle_field(frm) {
    if (frm.doc.document == 0 || !frm.doc.document) {
        // Hide & make not mandatory
        frm.set_df_property("bank", "hidden", 1);
        frm.set_df_property("bank", "reqd", 0);
        frm.set_value("bank", null); // optional: clear value
        frm.set_df_property("term_days", "hidden", 1);
        frm.set_df_property("term_days", "reqd", 0);
        frm.set_value("term_days", null); // optional: clear value
        frm.set_df_property("bank_ref_no", "hidden", 1);
        frm.set_df_property("bank_ref_no", "reqd", 0);
        frm.set_value("bank_ref_no", null); // optional: clear value
        frm.set_df_property("payment_term", "reqd", 0);
    } else {
        // Show & make mandatory
        frm.set_df_property("bank", "hidden", 0);
        frm.set_df_property("bank", "reqd", 1);
        frm.set_df_property("term_days", "hidden", 0);
        frm.set_df_property("term_days", "reqd", 1);
        frm.set_df_property("bank_ref_no", "hidden", 0);
        frm.set_df_property("payment_term", "reqd", 1);
    }
}


frappe.ui.form.on("Shipping Book", {
    onload(frm){
        check_and_lock_fields(frm);
    },
	inv_no(frm) {
        validate_inv_no(frm);
    },
    refresh(frm) {
        apply_payment_term_filter(frm);
        toggle_field(frm);
    },

    document(frm) {
        frm.set_value("payment_term", null); // clear invalid value
        apply_payment_term_filter(frm);
        toggle_field(frm)
    }
});
