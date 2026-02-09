// // Copyright (c) 2025, SSDolui and contributors
// // For license information, please see license.txt


// =================================================================
// 1. HELPER FUNCTIONS (Must be defined at the top-level scope)
// =================================================================

// Helper function to reliably calculate the difference in days using native JS.
const calculateDaysDifference = (endDateStr, startDateStr) => {
    // Standard approach: Use T00:00:00 to prevent timezone issues.
    const endDate = new Date(endDateStr + 'T00:00:00');
    const startDate = new Date(startDateStr + 'T00:00:00');
    
    // Difference in milliseconds
    const diff_ms = endDate.getTime() - startDate.getTime();
    
    // Conversion factor (milliseconds in a day)
    const ms_per_day = 1000 * 60 * 60 * 24;
    
    // Return the difference in days, rounded to handle potential floating point issues
    return Math.round(diff_ms / ms_per_day);
};

// Query filter function
function inv_no_filter(frm) {
    frm.set_query('inv_no', () => ({
        query: 'ssd_app.my_custom.doctype.doc_received_details.doc_received_details.get_available_inv_no'
    }));
}


// =================================================================
// 2. MAIN LOGIC FUNCTIONS
// =================================================================

/**
 * Calculates the interest days and sets the 'interest_days' field.
 */
function calculate_interest_days(frm) {
    let days = 0; // Default days to 0
    
    // Check if both required dates exist
    if (frm.doc.received_date && frm.doc.interest_from && frm.doc.interest_on) {
        // End Date (later) is received_date, Start Date (earlier) is interest_from
        days = calculateDaysDifference(frm.doc.received_date, frm.doc.interest_from);  
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

    }
    
    // Set the calculated value back to the form field
    frm.set_value("interest", interest);
    
    // Crucial: After interest is calculated, the bank amount must be updated
    calculate_bank_amount(frm);
}


/**
 * Calculates the final bank amount after deductions and sets the 'bank_amount' field.
 */
function calculate_bank_amount(frm) {
    let bank_amount = 0; 
    
    // Helper to safely get the numerical value, defaulting to 0 if falsy (null, undefined, etc.)
    const get_safe_value = (field_name) => (frm.doc[field_name] || 0);

    // Get safe numerical values for all fields
    const received_amount = get_safe_value('received_amount');
    const interest = get_safe_value('interest');
    const bank_charge = get_safe_value('bank_charge');
    const commission = get_safe_value('commission');
    const postage = get_safe_value('postage');
    const cable_charges = get_safe_value('cable_charges');
    const discrepancy_charges = get_safe_value('discrepancy_charges');
    const short_payment = get_safe_value('short_payment');
    const foreign_charges = get_safe_value('foreign_charges');
    const bank_liability = get_safe_value('bank_liability');

    // Perform the calculation
    bank_amount = (
        received_amount - 
        interest - 
        bank_charge - 
        commission -
        postage -
        cable_charges -
        discrepancy_charges - 
        short_payment - 
        foreign_charges - 
        bank_liability
    );

    // Use the calculated local variable 'bank_amount' to update the form field.
    frm.set_value("bank_amount", bank_amount);
}

// Fetches negotiation and liability data from the server and updates the form.
function get_rec_data(frm) {
    if (!frm.doc.inv_no) return;

    // Only run this when creating a new document (to fetch default values)

    frappe.call({
        method: "ssd_app.my_custom.doctype.doc_nego.doc_nego.get_doc_int_summary",
        args: { 
            id_name:"rec",
            id: frm.doc.inv_no
        },
        callback: function (r) {
            const data = r.message;
            console.log(data.rec_amount);
            if (!data) return;

            // --- 1. Set values fetched from the server ---
            frm.set_value({
                received_amount: data.rec_amount,
                bank_liability: data.b_liab || 0,
                received_date: data.rec_date,
                bank: data.bank_name,
                interest_on: data.b_liab || 0, 
                interest_from: data.int_upto,
                interest_pct :data.int_pct
            });

            if (frm.is_new){
                frm.set_value(interest_pct, data.int_pct || 0);
                calculate_interest_days(frm);
                calculate_interest(frm);
                calculate_bank_amount(frm); // Call bank amount calculation

            }


        }
    });
    
    if (!frm.is_new()){
        frm.set_df_property('inv_no', "read_only", true);
    }
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



// =================================================================
// 3. FRAPPE HOOKS
// =================================================================

frappe.ui.form.on("Doc Received Details", {
    setup(frm) {
        inv_no_filter(frm);
    },
    // Triggers on load to fetch data and then calculate days
    onload(frm) {
        get_rec_data(frm);
        calculate_bank_amount(frm);
        calculate_interest_upto_date(frm);
    },
    // Triggers when inv_no is set/changed (fetches data and recalculates)
    inv_no(frm) {
        get_rec_data(frm); 
        calculate_interest(frm);
        calculate_bank_amount(frm);
        calculate_interest_upto_date(frm);
    },

    // --- Hooks for Interest Calculation Dependencies ---
  
    interest_on(frm) {
        calculate_interest(frm);
    },
    interest_days(frm) {
        calculate_interest(frm);
        calculate_interest_upto_date(frm);
    },
    interest_pct(frm) {
        calculate_interest(frm);
    },
    
    // --- Hooks for Bank Amount Calculation Dependencies ---
    // Note: Since calculate_interest() calls calculate_bank_amount() internally,
    // we only need a hook for 'interest' if the user were to manually edit it, 
    // but the following hooks are essential for direct input fields.
    
    received_amount(frm) {
        calculate_bank_amount(frm);
    },
    bank_charge(frm) {
        calculate_bank_amount(frm);
    },
    commission(frm) {
        calculate_bank_amount(frm);
    },
    postage(frm) {
        calculate_bank_amount(frm);
    },
    cable_charges(frm) {
        calculate_bank_amount(frm);
    },
    discrepancy_charges(frm) {
        calculate_bank_amount(frm);
    },
    short_payment(frm) {
        calculate_bank_amount(frm);
    },
    foreign_charges(frm) {
        calculate_bank_amount(frm);
    },
    bank_liability(frm) {
        // bank_liability is often linked to interest_on, so run both calculations
        calculate_interest(frm);
        calculate_bank_amount(frm);
    },
    interest(frm) {
        // This runs only if interest is manually changed, otherwise it's handled by calculate_interest
        calculate_bank_amount(frm);
    },
    after_save: function(frm) {
        // Redirect to the report page after save
        window.location.href = "/app/query-report/Doc Entry";
    }
});