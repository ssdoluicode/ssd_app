// // Copyright (c) 2025, SSDolui and contributors
// // For license information, please see license.txt


function lc_id_filter(frm) {
    frm.set_query('lc_id', () => ({
        query: 'ssd_app.my_custom.doctype.lc_payment_details.lc_payment_details.lc_id_filter'
    }));
}

// 🧠 Fetch negotiation data based on selected lc_payment_id
function get_lc_data(frm) {
    if (!frm.doc.lc_payment_id) return;

    // Only fetch if it's a new document to avoid overwriting existing data
    if (frm.is_new()) {
        frappe.call({
            method: "ssd_app.my_custom.doctype.lc_payment_details.lc_payment_details.get_lc_data",
            args: { lc_payment_id: frm.doc.lc_payment_id },
            callback: function (r) {
                if (r.message) {
                    const data = r.message;
                    frm.set_value({
                        payment_date: data.date,
                        company: data.com,
                        bank: data.bank_name,
                        currency: data.currency,
                        payment_amount: flt(data.amount) // Ensure it's treated as a number
                    });
                    // Recalculate bank amount after setting payment_amount
                    calculate_bank_amount(frm);
                }
            }
        });
    }
}

function set_amount_and_balance(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let rows = frm.doc.inv_details || [];
    let idx = row.idx - 1; // 1-based index

    if (idx === 0) {
        // Row 1 → default = amount_usd ONLY if empty
        if (!row.amount) row.amount = flt(frm.doc.payment_amount || 0);
    } else {
        let prev_row = rows[idx - 1];
        if (!row.amount) row.amount = flt(prev_row.balance || 0);
    }
}


function recalc_balance(frm) {

    let total = flt(frm.doc.payment_amount || 0);
    if (total <= 0) return;

    // Ensure at least one row
    if (!frm.doc.inv_details || frm.doc.inv_details.length === 0) {
        frm.add_child("inv_details", {
            amount: total
        });
    }

    let running_balance = total;

    frm.doc.inv_detailsx.forEach((row, idx) => {

        // Row 1 default → ONLY if empty
        if (idx === 0 && (!row.amount || row.amount === 0)) {
            row.amount = total;
        }

        // Row 2+ default → ONLY if empty
        else if (idx > 0 && (!row.amount || row.amount === 0)) {
            let prev_row = frm.doc.inv_details[idx - 1];
            row.amount = flt(prev_row.balance || 0);
        }

        // Always calculate balance
        row.balance = flt(running_balance - flt(row.amount || 0), 2);
        running_balance = row.balance;
    });

    frm.refresh_field("inv_details");

    // Disable Add Row if balance = 0
    frm.fields_dict.inv_details.grid.cannot_add_rows =
        Math.abs(running_balance) < 0.01;

    // Save control
    if (Math.abs(running_balance) < 0.01) {
        frm.enable_save();
        frm.set_df_property("inv_details", "description", "");
    } else {
        frm.disable_save();
        frm.set_df_property(
            "inv_details",
            "description",
            `<b style="color:red">Remaining Balance: ${running_balance.toFixed(2)}</b>`
        );
    }
}



function calculate_bank_amount(frm) {
    const payment = flt(frm.doc.payment_amount);
    const charges = flt(frm.doc.bank_charge);
    
    // Logic: Total Bank Outflow = Payment to LC + Bank Charges
    const total = payment + charges;

    // Set value with precision 2 (Standard for Bank/Currency fields)
    frm.set_value("bank_amount", flt(total, 2));
}

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
    }
});


/* ===============================
   CHILD TABLE TRIGGERS
   =============================== */
frappe.ui.form.on("LC Payment Details Inv Break", {

    supplier(frm, cdt, cdn) {
        set_amount_and_balance(frm, cdt, cdn);
        recalc_balance(frm);
    }
});