// 🧠 Function to apply custom query filter on inv_no field
function inv_no_filter(frm) {
    frm.set_query('inv_no', () => ({
        query: 'ssd_app.my_custom.doctype.doc_received.doc_received.get_available_inv_no'
    }));
}

function handle_bank_text_visibility(frm, bank, bank_name) {

    if (bank) {
        // ---- Bank exists ----
        frm.toggle_display("bank", true);
        frm.set_value("bank", bank_name || "");
        frm.set_df_property("bank_text", "read_only", 1);

        frm.toggle_display("bank_link", false);
        frm.set_value("bank_link", "");
        frm.set_df_property("bank_link", "reqd", 0);

    } else {
        // ---- Bank does NOT exist ----
        frm.toggle_display("bank", false);
        frm.set_df_property("bank", "read_only", 0);

        frm.toggle_display("bank_link", true);
        frm.set_value("bank_link", "");
        frm.set_df_property("bank_link", "reqd", 1); 
    }
}

// 🧠 Function to fetch CIF data based on selected inv_no
function get_shi_data(frm) {
    if (!frm.doc.inv_no) return;

    if (frm.is_new() && !frappe.quick_entry) {
        frappe.call({
            method: "ssd_app.my_custom.doctype.doc_received.doc_received.get_shi_data",
            args: { inv_no: frm.doc.inv_no },
            callback: function (r) {
                const data = r.message;
                if (!data) return;

                frm.set_value({
                    inv_date: data.bl_date,
                    category: data.category,
                    notify: data.notify_name,
                    customer: data.customer_name,
                    bank: data.bank_name,
                    payment_term: data.payment_term_name,
                    term_days: data.term_days,
                    document: data.document,
                    received: data.receivable,
                    received_date: frappe.datetime.get_today()
                });
                handle_bank_text_visibility(frm, data.bank, data.bank_name)
            }
        });
    }
}


// 🧩 Main Form Event Bindings
frappe.ui.form.on("Doc Received", {
    onload(frm) {
        inv_no_filter(frm);  // ✅ Register custom filter
        get_shi_data(frm);  
    },
    inv_no(frm) {
        get_shi_data(frm);   // ✅ Fetch CIF details
    },
    after_save: function(frm) {
        // Redirect to the report page after save
        window.location.href = "/app/query-report/Document Receivable";
    }
});
