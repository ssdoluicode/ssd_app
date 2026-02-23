// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

// =================================================================
// Helper: Calculate days difference safely
// =================================================================

const calculateDaysDifference = (endDateStr, startDateStr) => {
    const endDate = new Date(endDateStr + 'T00:00:00');
    const startDate = new Date(startDateStr + 'T00:00:00');
    const diff_ms = endDate.getTime() - startDate.getTime();
    const ms_per_day = 1000 * 60 * 60 * 24;
    return Math.max(0, Math.round(diff_ms / ms_per_day));
};

// =================================================================
// Interest Days
// =================================================================

function calculate_interest_days(frm) {
    if (frm.doc.interest_days) {
        return;
    }
    let days = 0;
    if (frm.doc.received_date && frm.doc.interest_from && frm.doc.interest_on) {
        days = calculateDaysDifference(
            frm.doc.received_date,
            frm.doc.interest_from
        );
    }
    frm.set_value("interest_days", days);
}

// =================================================================
// Interest Calculation
// =================================================================
function calculate_interest(frm) {

    let interest = 0;

    if (frm.doc.interest_on && frm.doc.interest_days && frm.doc.interest_pct) {

        const calculated_interest =
            flt(frm.doc.interest_on) *
            flt(frm.doc.interest_days) *
            flt(frm.doc.interest_pct) /
            100 /
            360;

        interest = flt(calculated_interest, 2);
    }

    frm.set_value("interest", interest);
}

// =================================================================
// Bank Amount Calculation
// =================================================================

function calculate_bank_amount(frm) {

    const get = (f) => flt(frm.doc[f]);

    const bank_amount =
        get('received_amount') -
        get('interest') -
        get('bank_charge') -
        get('commission') -
        get('postage') -
        get('cable_charges') -
        get('discrepancy_charges') -
        get('short_payment') -
        get('foreign_charges') -
        get('bank_liability');

    frm.set_value("bank_amount", flt(bank_amount, 2));
}

// =================================================================
// Interest Upto Date
// =================================================================

function calculate_interest_upto_date(frm) {

    if (!frm.doc.interest_from) return;

    let from_date = new Date(frm.doc.interest_from + "T00:00:00");
    let days = flt(frm.doc.interest_days);

    let upto = new Date(from_date);
    upto.setDate(upto.getDate() + days);

    frm.set_value(
        "interest_upto_date",
        frappe.datetime.obj_to_str(upto)
    );
}

// =================================================================
// Invoice Filter
// =================================================================

function inv_no_filter(frm) {
    frm.set_query('inv_no', () => ({
        query: 'ssd_app.my_custom.doctype.doc_received_details.doc_received_details.get_available_inv_no'
    }));
}

// =================================================================
// Fetch Server Data (Modern Async Version)
// =================================================================

async function get_rec_data(frm) {

    if (!frm.doc.inv_no) return;

    const r = await frappe.call({
        method: "ssd_app.my_custom.doctype.doc_nego.doc_nego.get_doc_int_summary",
        args: {
            id_name: "rec",
            id: frm.doc.inv_no
        }
    });

    const data = r.message;
    if (!data) return;

    // Always set these
    await frm.set_value({
        received_amount: data.rec_amount,
        received_date: data.rec_date,
        bank: data.bank_name
    });

    // Only for NEW doc
    if (frm.is_new()) {
        await frm.set_value({
            bank_liability: data.b_liab || 0,
            interest_on: data.b_liab || 0,
            interest_from: data.int_upto,
            interest_pct: data.int_pct || 0
        });

        calculate_interest_days(frm);
        calculate_interest(frm);
        calculate_interest_upto_date(frm);
    }

    if (!frm.is_new()) {
        frm.set_df_property('inv_no', "read_only", true);
    }
}

// =================================================================
// FRAPPE EVENTS
// =================================================================

frappe.ui.form.on("Doc Received Details", {

    setup(frm) {
        inv_no_filter(frm);
    },

    async onload(frm) {
        if (frm.doc.inv_no) {
            await get_rec_data(frm);
        }
    },

    async inv_no(frm) {
        await get_rec_data(frm);
    },

    // Interest dependency chain
    interest_days(frm) {
        calculate_interest(frm);
        calculate_interest_upto_date(frm);
        calculate_bank_amount(frm);
    },

    interest_pct(frm) {
        calculate_interest(frm);
        calculate_bank_amount(frm);
    },

    interest(frm) {
        calculate_bank_amount(frm);
    },

    // Direct bank amount dependencies
    received_amount: calculate_bank_amount,
    bank_charge: calculate_bank_amount,
    commission: calculate_bank_amount,
    postage: calculate_bank_amount,
    cable_charges: calculate_bank_amount,
    discrepancy_charges: calculate_bank_amount,
    short_payment: calculate_bank_amount,
    foreign_charges: calculate_bank_amount,

    after_save(frm) {
        window.location.href = "/app/query-report/Doc Entry";
    }

});