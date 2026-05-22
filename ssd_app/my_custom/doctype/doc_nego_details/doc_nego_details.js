function inv_no_filter(frm) {
    frm.set_query('inv_no', () => ({
        query: 'ssd_app.my_custom.doctype.doc_nego_details.doc_nego_details.get_available_inv_no'
    }));
}

// 🧠 Fetch negotiation data based on selected inv_no
function get_nego_data(frm) {
    if (!frm.doc.inv_no) return;
    frappe.call({
        method: "ssd_app.my_custom.doctype.doc_nego_details.doc_nego_details.get_nego_data",
        args: { name: frm.doc.inv_no },
        callback: function (r) {
            const data = r.message;
            if (!data) return;

            frm.set_value({
                nego_amount: data.nego_amount,
                nego_date: data.nego_date,
                bank:data.bank_name,
                payment_term: data.payment_term
            });
        }
    });
    
}

// 💰 Calculate interest and due date
function calculate_int(frm) {
    if (frm.doc.nego_amount && frm.doc.interest_pct && frm.doc.interest_days) {
        let interest = (frm.doc.nego_amount * frm.doc.interest_pct * frm.doc.interest_days) / (360 * 100);
        interest = flt(interest, 2); // ✅ safely round to 2 decimals
        frm.set_value('interest', interest);
    }
}

// 📅 Calculate interest upto date
function calculate_interest_upto_date(frm) {
    if (frm.doc.nego_date) {
        let nego_date = frappe.datetime.str_to_obj(frm.doc.nego_date);
        let due_date = frappe.datetime.add_days(nego_date, frm.doc.interest_days);
        frm.set_value('interest_upto_date', frappe.datetime.obj_to_str(due_date));
    }
}

// 💼 Calculate commission
function calculate_comm(frm) {
    if (frm.doc.nego_amount && frm.doc.commission_pct && frm.doc.min_comm==0) {
        let commission = (frm.doc.nego_amount * frm.doc.commission_pct) / 100;
        commission = flt(commission, 2);
        frm.set_value('commission', commission);
    }
}

function if_min_comm(frm){
    if (frm.doc.min_comm==1){
        frm.set_value("commission",0)
        frm.set_value("commission_pct",0)
        frm.set_df_property("commission_pct", "read_only", 1);
        frm.set_df_property("commission", "read_only", 0);
    }else{
        frm.set_df_property("commission_pct", "read_only", 0);
        frm.set_df_property("commission", "read_only", 1);
    }
}

// 🏦 Calculate bank amount
function calculate_bank_amount(frm) {
    if (frm.doc.nego_amount) {
        // Safely convert all to floats
        let nego_amount = flt(frm.doc.nego_amount);
        let interest = flt(frm.doc.interest);
        let commission = flt(frm.doc.commission);
        let postage_charges = flt(frm.doc.postage_charges);
        let other_charges = flt(frm.doc.other_charges);
        let round_off = flt(frm.doc.round_off);

        // Calculate and round
        let bank_amount = nego_amount - interest - commission - postage_charges - other_charges - round_off;
        bank_amount = flt(bank_amount, 2);

        frm.set_value('bank_amount', bank_amount);
    }
}

// 🧩 Main event handlers
frappe.ui.form.on("Doc Nego Details", {
    setup(frm) {
        inv_no_filter(frm);
    },

    onload(frm) {
        get_nego_data(frm);
    },
    inv_no(frm) {
        get_nego_data(frm);
        calculate_int(frm);
        calculate_comm(frm);
        calculate_bank_amount(frm);
    },
    interest_days(frm) {
        calculate_int(frm);
        calculate_bank_amount(frm);
    },
    interest_pct(frm) {
        calculate_int(frm);
        calculate_bank_amount(frm);
    },
    commission_pct(frm) {
        calculate_comm(frm);
        calculate_bank_amount(frm);
    },
    commission(frm) {
        calculate_comm(frm);
        calculate_bank_amount(frm);
    },
    postage_charges(frm) {
        calculate_bank_amount(frm);
    },

    other_charges(frm) {
        calculate_bank_amount(frm);
    },
    round_off(frm) {
        calculate_bank_amount(frm);
    },
    min_comm(frm){
        if_min_comm(frm);
        calculate_comm(frm);
    },
    // nego_amount(frm) {
    //     // ✅ Recalculate everything when main amount changes
    //     calculate_int(frm);
    //     calculate_comm(frm);
    //     calculate_bank_amount(frm);
    // },

    nego_date(frm) {
        // ✅ Recalculate interest due date when base date changes
        calculate_int(frm);
    },
    before_save(frm){
        calculate_interest_upto_date(frm);
    },
    // after_save: function(frm) {
    //     // Redirect to the report page after save
    //     window.location.href = "/app/query-report/Doc Entry";
    // }
    after_save(frm) {
        const returnTo = sessionStorage.getItem('return_to_after_save');
        
        if (returnTo === 'Doc Entry') {
            sessionStorage.removeItem('return_to_after_save');

            // This is the fastest safe way in v15
            frappe.run_serially([
                // 1. Wait a tiny bit for the save UI to settle (200ms is fine here)
                () => frappe.timeout(0.2), 
                
                // 2. Change the route (Internal redirect, no full reload)
                () => frappe.set_route("query-report", returnTo),
                
                // 3. Refresh the report data immediately upon arrival
                () => {
                    if (frappe.query_report && frappe.query_report.report_name === returnTo) {
                        frappe.query_report.refresh();
                    }
                }
            ]);
        }
    }
});
