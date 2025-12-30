// // // Copyright (c) 2025, SSDolui and contributors
// // // For license information, please see license.txt


function lc_id_filter(frm) {
    frm.set_query("lc_payment_id", () => ({
        query: "ssd_app.my_custom.doctype.lc_payment_details.lc_payment_details.lc_id_filter"
    }));
}

// Fetch LC data
function get_lc_data(frm) {
    if (!frm.doc.lc_payment_id) return;

    // Fetch only for new document
    if (frm.is_new()) {
        frappe.call({
            method: "ssd_app.my_custom.doctype.lc_payment_details.lc_payment_details.get_lc_data",
            args: {
                lc_payment_id: frm.doc.lc_payment_id
            },
            callback(r) {
                if (r.message) {
                    const data = r.message;

                    frm.set_value({
                        payment_date: data.date,
                        company: data.com,
                        bank: data.bank_name,
                        currency: data.currency,
                        payment_amount: flt(data.amount)
                    });

                    calculate_bank_amount(frm);
                }
            }
        });
    }
}


/* ===============================
   BANK AMOUNT
   =============================== */

function calculate_bank_amount(frm) {
    const payment = flt(frm.doc.payment_amount || 0);
    const charges = flt(frm.doc.bank_charge || 0);

    frm.set_value("bank_amount", flt(payment + charges, 2));
}

/* ===============================
   PARENT FORM EVENTS
   =============================== */

frappe.ui.form.on("LC Payment Details", {

    setup(frm) {
        lc_id_filter(frm);
    },

    lc_payment_id(frm) {
        get_lc_data(frm);
    },

    payment_amount(frm) {
        calculate_bank_amount(frm);
    },

    bank_charge(frm) {
        calculate_bank_amount(frm);
    },
    after_save: function(frm) {
        // Redirect to the report page after save
        window.location.href = "/app/query-report/Import Banking Entry";
    }
});

