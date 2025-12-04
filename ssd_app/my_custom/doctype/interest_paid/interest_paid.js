// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt



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


function get_nego_data(frm) {
    if (!frm.doc.inv_no || !frm.doc.date) return;

    // Run ONLY in New Form
    if (frm.is_new() && !frappe.quick_entry) {
        frappe.call({
            method: "ssd_app.my_custom.doctype.doc_nego.doc_nego.get_cif_summary",
            args: {
                id_name:"nego",
                id: frm.doc.inv_no,
                as_on: frm.doc.date
            },
            callback: function (r) {
                if (!r.message) return;

                const data = r.message;

                frm.set_value({
                    balance_nego_amount: data.b_liab,
                    interest_from: data.int_upto,
                    interest_rate: data.int_pct
                });
            }
        });
    }
}



function calculate_interest_upto_date(frm){
    if (frm.doc.interest_from && frm.doc.interest_days) {
            let int_from = frappe.datetime.str_to_obj(frm.doc.interest_from);
            let int_upto = frappe.datetime.add_days(int_from, frm.doc.interest_days);
            frm.set_value('interest_upto_date', frappe.datetime.obj_to_str(int_upto));
        }
    }

function calculate_int(frm) {
    if (frm.doc.balance_nego_amount && frm.doc.interest_rate && frm.doc.interest_days) {
        let interest = (frm.doc.balance_nego_amount * frm.doc.interest_rate * frm.doc.interest_days) / (360 * 100);
        interest = flt(interest, 2)+ frm.doc.round_off; // ✅ safely round to 2 decimals
        frm.set_value('interest', interest);
    }
}

function calculate_interest_days(frm) {
    let days = 0; // Default days to 0
    
    // Check if both required dates exist
    if (frm.doc.date && frm.doc.interest_from) {
        // End Date (later) is received_date, Start Date (earlier) is interest_from
        days = calculateDaysDifference(frm.doc.date, frm.doc.interest_from);  
    }
    frm.set_value("interest_days", days);
}


frappe.ui.form.on("Interest Paid", {
	inv_no(frm) {
        get_nego_data(frm);
    },
    date(frm) {
        get_nego_data(frm);
        calculate_interest_days(frm);
    },
    balance_nego_amount(frm){
        calculate_int(frm);
    },
    interest_from(frm) {
        calculate_interest_upto_date(frm);
        calculate_int(frm);
        calculate_interest_days(frm);
    },
    interest_rate(frm){
        calculate_int(frm);
    },
    round_off(frm){
        calculate_int(frm);
    },
    interest_days(frm){
        calculate_interest_upto_date(frm)
        calculate_int(frm);
    },
    after_save: function(frm) {
        // Redirect to the report page after save
        window.location.href = "/app/query-report/Doc Entry";
    }
});
