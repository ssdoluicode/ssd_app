// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

// Helper function to reliably calculate the difference in days using native JS.
const calculateDaysDifference = (endDateStr, startDateStr) => {
    const endDate = new Date(endDateStr + 'T00:00:00');
    const startDate = new Date(startDateStr + 'T00:00:00');
    const diff_ms = endDate.getTime() - startDate.getTime();
    const ms_per_day = 1000 * 60 * 60 * 24;
    return Math.round(diff_ms / ms_per_day);
};



function inv_no_filter(frm) {
    frm.set_query('inv_no', () => ({
        query: 'ssd_app.my_custom.doctype.doc_refund_details.doc_refund_details.get_available_inv_no'
    }));
}

// Fetches negotiation and liability data from the server and updates the form.
function get_ref_data(frm) {
    if (!frm.doc.inv_no) return;

    // Only run this when creating a new document (to fetch default values)
    
    frappe.call({
        method: "ssd_app.my_custom.doctype.doc_nego.doc_nego.get_doc_int_summary",
        args: { 
            id_name:"ref",
            id: frm.doc.inv_no
        },
        callback: function (r) {
            const data = r.message;
            if (!data) return;

            // --- 1. Set values fetched from the server ---
            frm.set_value({
                refund_amount: data.ref_amount,
                refund_date: data.ref_date,
                bank: data.bank_name,
                interest_on: data.b_liab || 0, 
                interest_from: data.int_upto,
                interest_pct :data.int_pct
            });

            // --- 2. ASYNCHRONOUS DEPENDENCY: Recalculate all dependencies ---
            calculate_interest_days(frm);
            calculate_interest(frm);
            calculate_bank_amount(frm); // Call bank amount calculation
        }
    });
  
    if (!frm.is_new()) {
        frm.set_df_property('inv_no', "read_only", true);
    }
}



/**
 * Calculates the interest days and sets the 'interest_days' field.
 */
function calculate_interest_days(frm) {
    let days = 0; // Default days to 0
    
    // Check if both required dates exist
    if (frm.doc.refund_date && frm.doc.interest_from) {
        // End Date (later) is received_date, Start Date (earlier) is interest_from
        days = calculateDaysDifference(frm.doc.refund_date, frm.doc.interest_from);  
    }
    frm.set_value("interest_days", days);
}


/**
 * Calculates the interest amount, rounds it to 2 decimal places, and sets the 'interest' field.
 */
function calculate_interest(frm) {
    let interest = 0; // Initialize interest to 0
    
    // Check if all required fields exist
    if (frm.doc.interest_on && frm.doc.interest_days && frm.doc.interest_pct) {
        
        // Perform the raw calculation
        const calculated_interest = frm.doc.interest_on * frm.doc.interest_days * frm.doc.interest_pct / 100 / 360;
        
        // Round the result to 2 decimal places and convert back to a number
        interest = parseFloat(calculated_interest.toFixed(2));
        interest += frm.doc.round_off

    }
    
    // Set the calculated value back to the form field
    frm.set_value("interest", interest);
    
    // Crucial: After interest is calculated, the bank amount must be updated
    calculate_bank_amount(frm);
}


function calculate_bank_amount(frm) {
    let bank_amount = 0; 
    
    // Helper to safely get the numerical value, defaulting to 0 if falsy (null, undefined, etc.)
    const get_safe_value = (field_name) => (frm.doc[field_name] || 0);

    // Get safe numerical values for all fields
    const refund_amount = get_safe_value('refund_amount');
    const interest = get_safe_value('interest');
    const bank_charges = get_safe_value('bank_charges');

    // Perform the calculation
    bank_amount = (
        refund_amount + 
        interest + 
        bank_charges
    );

    // Use the calculated local variable 'bank_amount' to update the form field.
    frm.set_value("bank_amount", bank_amount);
}

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

frappe.ui.form.on("Doc Refund Details", {
	setup(frm) {
        inv_no_filter(frm);
    },
    // Triggers on load to fetch data and then calculate days
    onload(frm) {
        get_ref_data(frm);
        calculate_bank_amount(frm);
        calculate_interest_upto_date(frm);
    },
    // Triggers when inv_no is set/changed (fetches data and recalculates)
    inv_no(frm) {
        get_ref_data(frm); 
        calculate_interest(frm);
        calculate_bank_amount(frm);
        calculate_interest_upto_date(frm);
        
    },
    interest_from(frm) {
        calculate_interest_days(frm);
        calculate_interest(frm);
        calculate_bank_amount(frm);
        calculate_interest_upto_date(frm);
    },
    refund_date(frm) {
        calculate_interest_days(frm);
        calculate_bank_amount(frm);
    },
    interest_on(frm){
        calculate_interest(frm);
        calculate_bank_amount(frm);
    },
    interest_days(frm){
        calculate_interest(frm);
        calculate_bank_amount(frm);
        calculate_interest_upto_date(frm);
    },
    interest_pct(frm){
        calculate_interest(frm);
        calculate_bank_amount(frm);
    },
    interest_pct(frm){
        calculate_interest(frm);
        calculate_bank_amount(frm);
    },
    round_off(frm){
        calculate_interest(frm);
        calculate_bank_amount(frm);
    },
    bank_charges(frm){
        calculate_bank_amount(frm);
    },
    after_save: function(frm) {
        // Redirect to the report page after save
        window.location.href = "/app/query-report/Doc Entry";
    }



});
