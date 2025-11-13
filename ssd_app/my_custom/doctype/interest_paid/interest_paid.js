// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt


// 🧠 Fetch negotiation data based on selected inv_no
function get_nego_data(frm) {
    if (!frm.doc.inv_no || !frm.doc.date) return;

    if (frm.is_new() && !frappe.quick_entry) {
        frappe.call({
            method: "ssd_app.my_custom.doctype.interest_paid.interest_paid.get_nego_data",
            args: {inv_no: frm.doc.inv_no, date: frm.doc.date, name:frm.name },
            callback: function (r) {
                const data = r.message;
                if (!data) return;

                frm.set_value({
                    balance_nego_amount: data.nego_amount,
                    interest_from: data.last_interest_upto,
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
        interest = flt(interest, 2); // ✅ safely round to 2 decimals
        frm.set_value('interest', interest);
    }
}
frappe.ui.form.on("Interest Paid", {
	inv_no(frm) {
        get_nego_data(frm);
    },
    date(frm) {
        get_nego_data(frm);
    },
    balance_nego_amount(frm){
        calculate_int(frm);
    },
    interest_from(frm) {
        calculate_interest_upto_date(frm);
        calculate_int(frm);
    },
    interest_rate(frm){
        calculate_int(frm);
    },
    interest_days(frm){
        calculate_interest_upto_date(frm)
        calculate_int(frm);
    }
});
