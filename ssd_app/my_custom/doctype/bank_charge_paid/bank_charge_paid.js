// Copyright (c) 2026, SSDolui and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bank Charge Paid", {
    refresh(frm) {
        set_narration(frm);
    },
    bank_charge_type(frm) {
        set_narration(frm);
    },
    invoice_no(frm) {
        set_narration(frm);
    },
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

function set_narration(frm) {
    // Check if the document is NOT new (already saved in DB)
    const is_not_new = !frm.doc.__islocal;

    // If it's an existing record AND narration already has text, skip update
    if (is_not_new && frm.doc.narration) {
        return;
    }

    let narration = "";

    // 1. Determine the base narration text
    if (frm.doc.bank_charge_type === "EB" || frm.doc.bank_charge_type === "TT") {
        narration = "Being Bank Charge Paid";
    } else if (frm.doc.bank_charge_type === "IB") {
        narration = "Being LC Opening fees Paid";
    }

    // 2. Append invoice number only if a base narration exists and invoice_no is present
    if (narration && frm.doc.invoice_no) {
        narration += ` for invoice no ${frm.doc.invoice_no}`;
    }

    // 3. Set the value in the form field
    frm.set_value("narration", narration);
}