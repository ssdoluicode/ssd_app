/*************************************************
 * CC RECEIVED – FINAL STABLE CLIENT SCRIPT
 *************************************************/

frappe.ui.form.on("CC Received", {

    refresh(frm) {

        // Remove old handler (avoid duplicate binding)
        $(frm.wrapper).off('keydown.form_focus_loop');

        $(frm.wrapper).on('keydown.form_focus_loop', function (e) {

            if (e.key !== "Tab") return;

            let focusable = $(frm.wrapper)
                .find('input, select, textarea, button')
                .filter(':visible:not([disabled])');

            if (!focusable.length) return;

            let first = focusable.first()[0];
            let last  = focusable.last()[0];

            // SHIFT + TAB (reverse)
            if (e.shiftKey) {
                if (document.activeElement === first) {
                    e.preventDefault();
                    last.focus();
                }
            }
            // Normal TAB
            else {
                if (document.activeElement === last) {
                    e.preventDefault();
                    first.focus();
                }
            }
        });
    },

    amount(frm) {
        calculate_amount_usd(frm);
    },

    ex_rate(frm) {
        calculate_amount_usd(frm);
    },

    amount_usd(frm) {
        recalc_balance(frm);
    },

    cc_breakup_add(frm) {
        recalc_balance(frm);
    },

    cc_breakup_remove(frm) {
        recalc_balance(frm);
    },

    validate(frm) {
        let rows = frm.doc.cc_breakup || [];
        if (!rows.length) return;

        let last_balance = flt(rows[rows.length - 1].balance || 0);
        if (Math.abs(last_balance) > 0.01) {
            frappe.throw(
                __("Last row balance must be ZERO before saving.")
            );
        }
    }
});


/* ===============================
   CHILD TABLE TRIGGERS
   =============================== */
frappe.ui.form.on("CC Breakup", {

    // User edits amount → only recalc balance
    amount(frm) {
        recalc_balance(frm);
    },

    // Ref No changed → default amount + recalc balance
    ref_no(frm, cdt, cdn) {
        set_amount_from_previous_balance(frm, cdt, cdn);
        recalc_balance(frm);
    }
});


/* ===============================
   HEADER CALCULATION
   =============================== */
function calculate_amount_usd(frm) {
    if (!frm.doc.amount || !frm.doc.ex_rate) return;

    let usd = flt(frm.doc.amount) / flt(frm.doc.ex_rate);
    frm.set_value("amount_usd", flt(usd, 2));
}


/* ===============================
   SET AMOUNT FROM PREVIOUS BALANCE
   =============================== */
function set_amount_from_previous_balance(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let rows = frm.doc.cc_breakup || [];
    let idx = row.idx - 1; // 1-based index

    if (idx === 0) {
        // Row 1 → default = amount_usd ONLY if empty
        if (!row.amount) row.amount = flt(frm.doc.amount_usd || 0);
    } else {
        let prev_row = rows[idx - 1];
        if (!row.amount) row.amount = flt(prev_row.balance || 0);
    }
}


/* ===============================
   RECALCULATE BALANCE
   =============================== */
function recalc_balance(frm) {

    let total = flt(frm.doc.amount_usd || 0);
    if (total == 0) return;

    // Ensure at least one row
    if (!frm.doc.cc_breakup || frm.doc.cc_breakup.length === 0) {
        frm.add_child("cc_breakup", {
            ref_no: "On Account",
            amount: total
        });
    }

    let running_balance = total;

    frm.doc.cc_breakup.forEach((row, idx) => {

        // Row 1 default → ONLY if empty
        if (idx === 0 && (!row.amount || row.amount === 0)) {
            row.amount = total;
            row.ref_no= "On Account";
        }

        // Row 2+ default → ONLY if empty
        else if (idx > 0 && (!row.amount || row.amount === 0)) {
            let prev_row = frm.doc.cc_breakup[idx - 1];
            row.amount = flt(prev_row.balance || 0);
        }

        // // Cap amount
        // if (row.amount > running_balance) {
        //     row.amount = running_balance;
        // }

        // Always calculate balance
        row.balance = flt(running_balance - flt(row.amount || 0), 2);
        running_balance = row.balance;
    });

    frm.refresh_field("cc_breakup");

    // Disable Add Row if balance = 0
    frm.fields_dict.cc_breakup.grid.cannot_add_rows =
        Math.abs(running_balance) < 0.01;

    // Save control
    if (Math.abs(running_balance) < 0.01) {
        frm.enable_save();
        frm.set_df_property("cc_breakup", "description", "");
    } else {
        frm.disable_save();
        frm.set_df_property(
            "cc_breakup",
            "description",
            `<b style="color:red">Remaining Balance: ${running_balance.toFixed(2)}</b>`
        );
    }
}
