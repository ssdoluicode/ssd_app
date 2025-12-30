// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt


function apply_loan_id_filter(frm) {
    frm.set_query("import_loan_id", () => {
        return {
            query: "ssd_app.my_custom.doctype.import_loan_payment_details.import_loan_payment_details.loan_id_filter"
        };
    });
}

function get_imp_loan_data(frm) {
    if (frm.is_new() && frm.doc.import_loan_id) {
        frappe.call({
            method: "ssd_app.my_custom.doctype.import_loan_payment_details.import_loan_payment_details.get_imp_loan_data",
            args: {
                import_loan_id: frm.doc.import_loan_id
            },
            freeze: true,
            callback(r) {
                if (r.message) {
                    const data = r.message;

                    let days = 0;
                    if (data.date && data.interest_from) {
                        days = frappe.datetime.get_diff(data.date, data.interest_from);
                    }

                    // 1. Set values from server
                    frm.set_value({
                        "payment_date": data.date,
                        "company": data.com,
                        "bank": data.bank_name,
                        "currency": data.currency,
                        "payment_amount": flt(data.amount),
                        "interest_from": data.interest_from,
                        "interest_days": days,
                        "interest_pct": data.interest_pct,
                        "interest_on": data.interest_on,
                        "referance_inv_no": data.inv_no,
                        "prev_accrued_interest": data.prev_accrued_interest,
                        "loan_id": data.loan_id
                    }).then(() => {
                        // 2. Perform calculations ONLY AFTER values are set
                        calculate_interest(frm);
                        calculate_interest_upto(frm);
                        calculate_bank_amount(frm);
                    });
                }
            }
        });
    }
}

frappe.ui.form.on("Import Loan Payment Details", {
    setup(frm) {
        apply_loan_id_filter(frm);
    },
    refresh(frm) {
        apply_loan_id_filter(frm);
    },
    import_loan_id(frm) {
        get_imp_loan_data(frm);
    },
    // Triggers for manual changes
    round_off(frm) { calculate_all(frm); },
    interest_days(frm) { calculate_all(frm); },
    interest_pct(frm) { calculate_all(frm); },
    bank_charge(frm) { calculate_bank_amount(frm); },
    accrued_interest(frm) { calculate_bank_amount(frm); },
    after_save: function(frm) {
        // Redirect to the report page after save
        window.location.href = "/app/query-report/Import Banking Entry";
    }
});

// Helper to run full sequence
function calculate_all(frm) {
    calculate_interest(frm);
    calculate_interest_upto(frm);
    calculate_bank_amount(frm);
}

/* ===============================
   CALCULATIONS
   =============================== */

function calculate_interest(frm) {
    // Check if required values exist to avoid NaN
    if (frm.doc.interest_on && frm.doc.interest_pct && frm.doc.interest_days) {
        let interest = flt((frm.doc.interest_on * frm.doc.interest_pct * frm.doc.interest_days) / 360 / 100, 2);
        // Apply round off after interest calculation
        frm.set_value("interest", flt(interest - (frm.doc.round_off || 0), 2));
    }
}

function calculate_bank_amount(frm) {
    const payment = flt(frm.doc.payment_amount || 0, 2);
    const interest = flt(frm.doc.interest || 0, 2);
    const bank_charge = flt(frm.doc.bank_charge || 0, 2);
    const accrued_interest = flt(frm.doc.accrued_interest || 0, 2);
    const prev_accrued_interest = flt(frm.doc.prev_accrued_interest || 0, 2);

    let total = payment + prev_accrued_interest + interest + bank_charge - accrued_interest;
    frm.set_value("bank_amount", flt(total, 2));
}

function calculate_interest_upto(frm) {
    if (frm.doc.interest_from && frm.doc.interest_days) {
        let interest_upto = frappe.datetime.add_days(frm.doc.interest_from, frm.doc.interest_days);
        frm.set_value("interest_upto", interest_upto);
    }
}

