// // Copyright (c) 2025, SSDolui and contributors
// // For license information, please see license.txt


// // Helper function to reliably calculate the difference in days using native JS.
// const calculateDaysDifference = (endDateStr, startDateStr) => {
//     const endDate = new Date(endDateStr + 'T00:00:00');
//     const startDate = new Date(startDateStr + 'T00:00:00');
//     const diff_ms = endDate.getTime() - startDate.getTime();
//     const ms_per_day = 1000 * 60 * 60 * 24;
//     return Math.round(diff_ms / ms_per_day);
// };

// // Calculates the interest days and sets the 'interest_days' field.
// function calculate_interest_days(frm) {
//     // console.log(frm);
//     let days = 0;
//     console.log(frm.doc.received_date, frm.doc.interest_from);
//     if (frm.doc.received_date && frm.doc.interest_from ) {
//         days = calculateDaysDifference(frm.doc.received_date, frm.doc.interest_from);  
//     }
//     console.log(days);
//     frm.set_value("interest_days", days);
// }

// // Calculates the interest amount, rounds it to 2 decimal places, and sets the 'interest' field.

// function calculate_interest(frm) {
//     let interest = 0;
//     if (frm.doc.interest_on && frm.doc.interest_days && frm.doc.interest_pct) {
//         const calculated_interest = frm.doc.interest_on * frm.doc.interest_days * frm.doc.interest_pct / 100 / 360;
//         interest = parseFloat(calculated_interest.toFixed(2));
//     }
//     frm.set_value("interest", interest);
//     calculate_bank_amount(frm);
// }



// // Calculates the final bank amount after deductions and sets the 'bank_amount' field.

// function calculate_bank_amount(frm) {
//     let bank_amount = 0; 
    
//     const get_safe_value = (field_name) => (frm.doc[field_name] || 0);

//     const received_amount = get_safe_value('received_amount');
//     const interest = get_safe_value('interest');
//     const bank_charge = get_safe_value('bank_charge');
//     const commission = get_safe_value('commission');
//     const postage = get_safe_value('postage');
//     const cable_charges = get_safe_value('cable_charges');
//     const discrepancy_charges = get_safe_value('discrepancy_charges');
//     const short_payment = get_safe_value('short_payment');
//     const foreign_charges = get_safe_value('foreign_charges');
//     const bank_liability = get_safe_value('bank_liability');
//     bank_amount = (
//         received_amount - 
//         interest - 
//         bank_charge - 
//         commission -
//         postage -
//         cable_charges -
//         discrepancy_charges - 
//         short_payment - 
//         foreign_charges - 
//         bank_liability
//     );

//     frm.set_value("bank_amount", bank_amount);
// }


// // calculate interest_upto_date
// function calculate_interest_upto_date(frm) {
//     if (frm.doc.interest_from) {
//         let from_date = new Date(frm.doc.interest_from + "T00:00:00");
//         let days = Number(frm.doc.interest_days) || 0;

//         let upto = new Date(from_date);
//         upto.setDate(upto.getDate() + days);
//         frm.set_value("interest_upto_date", frappe.datetime.obj_to_str(upto));
//     }
// }

// // Query filter function
// function inv_no_filter(frm) {
//     frm.set_query('inv_no', () => ({
//         query: 'ssd_app.my_custom.doctype.doc_received_details.doc_received_details.get_available_inv_no'
//     }));
// }

// // Fetches negotiation and liability data from the server and updates the form.
// function get_rec_data(frm) {
//     if (!frm.doc.inv_no) return;
//     frappe.call({
//         method: "ssd_app.my_custom.doctype.doc_nego.doc_nego.get_doc_int_summary",
//         args: { 
//             id_name:"rec",
//             id: frm.doc.inv_no
//         },
//         callback: function (r) {
//             const data = r.message;
//             if (!data) return;
//             // --- 1. Set values fetched from the server ---
//             frm.set_value({
//                 received_amount: data.rec_amount,
//                 bank_liability: data.b_liab || 0,
//                 received_date: data.rec_date,
//                 bank: data.bank_name,
//                 interest_on: data.b_liab || 0, 
//                 interest_from: data.int_upto,
//                 interest_pct :data.int_pct
//             });

//             if (frm.is_new){
//                 frm.set_value("interest_pct", data.int_pct || 0);
//                 calculate_interest_days(frm);
//                 calculate_interest(frm);
//                 calculate_bank_amount(frm); // Call bank amount calculation
//                 calculate_interest_upto_date(frm);
//             }
//         }
//     });
    
//     if (!frm.is_new()){
//         frm.set_df_property('inv_no', "read_only", true);
//     }
// }

// // =================================================================
// // 3. FRAPPE HOOKS
// // =================================================================

// frappe.ui.form.on("Doc Received Details", {
//     setup(frm) {
//         inv_no_filter(frm);
//     },
//     // Triggers on load to fetch data and then calculate days
//     onload(frm) {
//         get_rec_data(frm);
       
//         // calculate_interest_upto_date(frm);
//     },
//     // Triggers when inv_no is set/changed (fetches data and recalculates)
//     inv_no(frm) {
//         get_rec_data(frm); 
//         calculate_interest(frm);
//         // calculate_interest_upto_date(frm);
//     },

//     // --- Hooks for Interest Calculation Dependencies ---
  
//     interest_days(frm) {
//         calculate_interest(frm);
//         calculate_interest_upto_date(frm);
//     },
//     interest_pct(frm) {
//         calculate_interest(frm);
//     },
    
//     // --- Hooks for Bank Amount Calculation Dependencies ---
//     // Note: Since calculate_interest() calls calculate_bank_amount() internally,
//     // we only need a hook for 'interest' if the user were to manually edit it, 
//     // but the following hooks are essential for direct input fields.
    
//     received_amount(frm) {
//         calculate_bank_amount(frm);
//     },
//     bank_charge(frm) {
//         calculate_bank_amount(frm);
//     },
//     commission(frm) {
//         calculate_bank_amount(frm);
//     },
//     postage(frm) {
//         calculate_bank_amount(frm);
//     },
//     cable_charges(frm) {
//         calculate_bank_amount(frm);
//     },
//     discrepancy_charges(frm) {
//         calculate_bank_amount(frm);
//     },
//     short_payment(frm) {
//         calculate_bank_amount(frm);
//     },
//     foreign_charges(frm) {
//         calculate_bank_amount(frm);
//     },
    
//     interest(frm) {
//         // This runs only if interest is manually changed, otherwise it's handled by calculate_interest
//         calculate_bank_amount(frm);
//     },
//     after_save: function(frm) {
//         // Redirect to the report page after save
//         window.location.href = "/app/query-report/Doc Entry";
//     }
// });

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
    let days = 0;

    if (frm.doc.received_date && frm.doc.interest_from) {
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
        bank_liability: data.b_liab || 0,
        received_date: data.rec_date,
        bank: data.bank_name
    });

    // Only for NEW doc
    if (frm.is_new()) {
        await frm.set_value({
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