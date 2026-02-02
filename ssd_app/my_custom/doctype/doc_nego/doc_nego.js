// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

function inv_no_filter(frm) {
    frm.set_query('inv_no', () => ({
        query: 'ssd_app.my_custom.doctype.doc_nego.doc_nego.get_available_inv_no'
    }));
}


function handle_bank_text_visibility(frm, term_days, bank, bank_name, p_term, p_term_name) {

    if (term_days!=0) {
        // ---- Bank exists ----
        frm.set_df_property("payment_term_days", "reqd", 0);
        frm.set_df_property("payment_term_days", "read_only", 1);
    } else {
        frm.set_df_property("payment_term_days", "reqd", 1); // 🔴 MANDATORY
        frm.set_df_property("payment_term_days", "read_only", 0);
    }
    if (bank) {
        // ---- Bank exists ----
        frm.toggle_display("bank_text", true);
        frm.set_value("bank_text", bank_name || "");
        frm.set_df_property("bank_text", "read_only", 1);

        frm.toggle_display("bank_link", false);
        frm.set_value("bank_link", "");
        frm.set_df_property("bank_link", "reqd", 0);

    } else {
        // ---- Bank does NOT exist ----
        frm.toggle_display("bank_text", false);
        frm.set_df_property("bank_text", "read_only", 0);

        frm.toggle_display("bank_link", true);
        frm.set_value("bank_link", "");
        frm.set_df_property("bank_link", "reqd", 1); // 🔴 MANDATORY
    }
    if (p_term) {
        // ---- Bank exists ----
        frm.toggle_display("payment_term_text", true);
        frm.set_value("payment_term_text", p_term_name || "");
        frm.set_df_property("payment_term_text", "read_only", 1);

        frm.toggle_display("payment_term_link", false);
        frm.set_value("payment_term_link", "");
        frm.set_df_property("payment_term_link", "reqd", 0);

    } else {
        // ---- Bank does NOT exist ----
        frm.toggle_display("payment_term_text", false);
        frm.set_df_property("payment_term_text", "read_only", 0);

        frm.toggle_display("payment_term_link", true);
        frm.set_value("payment_term_link", "");
        frm.set_df_property("payment_term_link", "reqd", 1); // 🔴 MANDATORY
    }
}


function get_shi_data(frm) {
    if (!frm.doc.inv_no) return;

    if (frm.is_new() && !frappe.quick_entry) {
        frappe.call({
            method: "ssd_app.my_custom.doctype.doc_nego.doc_nego.get_shi_data",
            args: { inv_no: frm.doc.inv_no },
            callback: function (r) {
                const data = r.message;
                console.log(data);
                if (!data) return;

                // Set values
                frm.set_value({
                    inv_date: data.inv_date,
                    bank: data.bank,
                    payment_term_days: data.term_days,
                    term_days: data.term_days,
                    nego_amount: data.can_nego,
                });

                // 🔁 Toggle bank_text visibility
                handle_bank_text_visibility(frm, data.term_days, data.bank, data.bank_name, data.payment_term, data.p_term_name)
            }
        });
    }
}


function calculate_term_days(frm) {
    if (!frm.doc.nego_date || !frm.doc.bank_due_date) return;

    const nego_date = frappe.datetime.str_to_obj(frm.doc.nego_date);
    const due_date  = frappe.datetime.str_to_obj(frm.doc.bank_due_date);

    if (due_date < nego_date) {
        frm.set_value('term_days', null);
        frappe.msgprint({
            title: __('Invalid Date'),
            indicator: 'red',
            message: __('Bank Due Date must be after Negotiation Date.')
        });
        return;
    }

    const days = frappe.datetime.get_diff(
        frm.doc.bank_due_date,
        frm.doc.nego_date
    );

    frm.set_value('term_days', days);
}


function calculate_due_date(frm) {
    // if (!frm.doc.nego_date  || frm.doc.bank_due_date) return;

    if (frm.doc.term_days < 0) {
        frm.set_value('bank_due_date', null);
        frappe.msgprint({
            title: __('Invalid Term Days'),
            indicator: 'red',
            message: __('Term Days must be a positive integer.')
        });
        return;
    }

    const due_date = frappe.datetime.add_days(
        frm.doc.nego_date,
        frm.doc.term_days
    );

    frm.set_value('bank_due_date', due_date);
}



frappe.ui.form.on("Doc Nego", {
	onload(frm) {
        inv_no_filter(frm);  // ✅ Register custom filter  
        get_shi_data(frm);
    },
    inv_no(frm) {
        get_shi_data(frm);   // ✅ Fetch CIF details
    },
    bank_due_date(frm){
        calculate_term_days(frm);
    },
    term_days(frm){
        calculate_due_date(frm);
    },
    nego_date(frm){
        calculate_due_date(frm);
    },

    after_save: function(frm) {
        // Redirect to the report page after save
        window.location.href = "/app/query-report/Document Receivable";
    }

});



