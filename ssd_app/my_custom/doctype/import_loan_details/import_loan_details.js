// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt


function loan_id_filter(frm) {
    frm.set_query("import_loan_id", () => ({
        query: "ssd_app.my_custom.doctype.import_loan_details.import_loan_details.loan_id_filter"
    }));
}

// Fetch LC data
function get_import_data(frm) {
    if (!frm.doc.import_loan_id) return;

    // Fetch only for new document
    if (frm.is_new()) {
        frappe.call({
            method: "ssd_app.my_custom.doctype.import_loan_details.import_loan_details.get_import_data",
            args: {
                import_loan_id: frm.doc.import_loan_id
            },
            callback(r) {
                if (r.message) {
                    const data = r.message;

                    frm.set_value({
                        loan_date: data.date,
                        company: data.com,
                        bank: data.bank_name,
                        currency: data.currency,
                        loan_amount: flt(data.amount),
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
    const payment = flt(frm.doc.loan_amount || 0);
    const charges = flt(frm.doc.bank_charge || 0);

    frm.set_value("bank_amount", flt(payment + charges, 2));
}

/* ===============================
   PARENT FORM EVENTS
   =============================== */

frappe.ui.form.on("Import Loan Details", {

    setup(frm) {
        loan_id_filter(frm);
    },

    import_loan_id(frm) {
        get_import_data(frm);
    },

    loan_amount(frm) {
        calculate_bank_amount(frm);

    },

    bank_charge(frm) {
        calculate_bank_amount(frm);
    }

});
