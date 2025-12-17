// Copyright (c) 2025
// SSDolui and contributors

function set_cc_received_query(frm) {
    frm.set_query("cc_received_id", () => ({
        query: "ssd_app.my_custom.doctype.cc_received_details.cc_received_details.get_available_id"
    }));
}

function fetch_cc_received_data(frm) {
    const id = frm.doc.cc_received_id;
    if (!id) return;

    frappe.call({
        method: "ssd_app.my_custom.doctype.cc_received_details.cc_received_details.get_cc_rec_data",
        args: { name: id },
        callback: (r) => {
            if (!r.message) return;

            const data = r.message;

            frm.set_value({
                date: data.date,
                customer: data.customer,
                amount: data.amount,
                payment_term: data.payment_term
            });

            calculate_bank_amount(frm);
        }
    });
}

function calculate_bank_amount(frm) {
    const amount = flt(frm.doc.amount);
    const charge = flt(frm.doc.bank_charge);

    frm.set_value("bank_amount", amount - charge);
}

function calculate_bank_charge(frm) {
    const amount = flt(frm.doc.amount);
    const bank_amount = flt(frm.doc.bank_amount);

    frm.set_value("bank_charge", amount - bank_amount);
}

frappe.ui.form.on("CC Received Details", {

    setup(frm) {
        set_cc_received_query(frm);
    },

    onload_post_render(frm) {
        fetch_cc_received_data(frm);
        calculate_bank_amount(frm);
    },

    cc_received_id(frm) {
        fetch_cc_received_data(frm);
    },

    bank_charge(frm) {
        calculate_bank_amount(frm);
    },

    amount(frm) {
        calculate_bank_amount(frm);
    },

    bank_amount(frm){
        calculate_bank_charge(frm);
    },
    
    after_save: function(frm) {
        // Redirect to the report page after save
        window.location.href = "/app/query-report/CC Entry";
        // frappe.set_route("query-report", "CC Entry");
    }
});
