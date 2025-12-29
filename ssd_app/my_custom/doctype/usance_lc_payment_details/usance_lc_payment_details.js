// // // Copyright (c) 2025, SSDolui and contributors
// // // For license information, please see license.txt


function lc_id_filter(frm) {
    frm.set_query("lc_payment_id", () => ({
        query: "ssd_app.my_custom.doctype.usance_lc_payment_details.usance_lc_payment_details.lc_id_filter"
    }));
}

// Fetch LC data
function get_lc_data(frm) {
    if (!frm.doc.lc_payment_id) return;

    // Fetch only for new document
    if (frm.is_new()) {
        frappe.call({
            method: "ssd_app.my_custom.doctype.usance_lc_payment_details.usance_lc_payment_details.get_lc_data",
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
                        payment_amount: flt(data.amount),
                        supplier: data.supplier,
                        referance_inv_no: data.inv_no
                
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
    // Use flt() to ensure values are treated as numbers
    // Use precision() to get the system's decimal setting for that field
    const payment = flt(frm.doc.payment_amount, precision("payment_amount"));
    const charges = flt(frm.doc.bank_charge, precision("bank_charge"));

    // Calculate and set the value with the correct field precision
    const total = flt(payment + charges, precision("bank_amount"));
    
    frm.set_value("bank_amount", total);
}

/* ===============================
   PARENT FORM EVENTS
   =============================== */

frappe.ui.form.on("Usance LC Payment Details", {

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
    }
});

/* ===============================
   CHILD TABLE EVENTS
   =============================== */

frappe.ui.form.on("Usance LC Payment Details Inv Break", {

    amount(frm) {
        recalc_balance(frm);
    },

    supplier(frm, cdt, cdn) {
        set_amount_and_balance(frm, cdt, cdn);
        recalc_balance(frm);
    }
});
