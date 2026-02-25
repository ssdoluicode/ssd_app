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
    return Math.round(diff_ms / ms_per_day);
};


// =================================================================
// Invoice Filter
// =================================================================
function inv_no_filter(frm) {
    frm.set_query('inv_no', () => ({
        query: 'ssd_app.my_custom.doctype.doc_refund_details.doc_refund_details.get_available_inv_no'
    }));
}


// =================================================================
// Interest Days
// =================================================================
function calculate_interest_days(frm) {
    if (frm.doc.interest_days) {
        return;
    }
    let days = 0; 
    if (frm.doc.refund_date && frm.doc.interest_from) {
        days = calculateDaysDifference(frm.doc.refund_date, frm.doc.interest_from);  
    }
    frm.set_value("interest_days", days);
}

// =================================================================
// Interest Calculation
// =================================================================
function calculate_interest(frm) {
    let interest = 0; 
    
    if (frm.doc.interest_on && frm.doc.interest_days && frm.doc.interest_pct) {
        const calculated_interest = frm.doc.interest_on * frm.doc.interest_days * frm.doc.interest_pct / 100 / 360;
        interest = parseFloat(calculated_interest.toFixed(2));
        interest += frm.doc.round_off
    }
    frm.set_value("interest", interest);
    calculate_bank_amount(frm);
}

// =================================================================
// Bank Amount Calculation
// =================================================================
function calculate_bank_amount(frm) {
    let bank_amount = 0; 
    const get_safe_value = (field_name) => (frm.doc[field_name] || 0);
    const refund_amount = get_safe_value('refund_amount');
    const interest = get_safe_value('interest');
    const bank_charges = get_safe_value('bank_charges');

    bank_amount = (
        refund_amount + 
        interest + 
        bank_charges
    );

    frm.set_value("bank_amount", bank_amount);
}

// =================================================================
// Interest Upto Date Calculation
// =================================================================
function calculate_interest_upto_date(frm) {
    if (frm.doc.interest_from) {
        let from_date = new Date(frm.doc.interest_from + "T00:00:00");
        let days = Number(frm.doc.interest_days) || 0;

        let upto = new Date(from_date);
        upto.setDate(upto.getDate() + days);

        // Correct line:
        frm.set_value("interest_upto_date", frappe.datetime.obj_to_str(upto));
    }
}



// =================================================================
// Fetch Server Data (Modern Async Version)
// =================================================================
async function get_ref_data(frm) {

    if (!frm.doc.inv_no) return;

    // Wait for server call
    const r = await frappe.call({
        method: "ssd_app.my_custom.doctype.doc_nego.doc_nego.get_doc_int_summary",
        args: { 
            id_name: "ref",
            id: frm.doc.inv_no
        }
    });

    const data = r.message;
    if (!data) return;

    // ✅ WAIT for values to be set
    await frm.set_value({
        refund_amount: data.ref_amount,
        refund_date: data.ref_date,
        bank: data.bank_name,
    });

    if (frm.is_new()) {
        await frm.set_value({
            interest_pct: data.int_pct,
            interest_on: data.b_liab || 0,
            interest_from: data.int_upto
        });

        // Now calculations will use updated values
        calculate_interest_days(frm);
        calculate_interest(frm);
        calculate_interest_upto_date(frm);
    }

    if (!frm.is_new()) {
        frm.set_df_property("inv_no", "read_only", true);
    }
}


// =================================================================
// FRAPPE EVENTS
// =================================================================
frappe.ui.form.on("Doc Refund Details", {
	setup(frm) {
        inv_no_filter(frm);
    },
    async onload(frm) {
        await get_ref_data(frm);
    },
    async inv_no(frm) {
        await get_ref_data(frm); 
    },
    interest_days(frm){
        calculate_interest(frm);
        calculate_interest_upto_date(frm);
    },
    interest_pct(frm){
        calculate_interest(frm);
    },
    round_off(frm){
        calculate_interest(frm);
    },
    bank_charges(frm){
        calculate_bank_amount(frm);
    },
    after_save: function(frm) {
        // Redirect to the report page after save
        window.location.href = "/app/query-report/Doc Entry";
    }



});
