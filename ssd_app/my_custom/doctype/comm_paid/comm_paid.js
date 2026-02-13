
frappe.ui.form.on('Comm Paid', {

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

    setup(frm) {
        frm.set_query('inv_no', 'comm_breakup', () => {
            return {
                query: "ssd_app.my_custom.doctype.comm_paid.comm_paid.get_filter_inv_no",
                filters: { agent: frm.doc.agent }
            };
        });
    },

    onload(frm) {
        // Automatically add a row if the child table is empty (New Doc only)
        if (frm.is_new() && (!frm.doc.comm_breakup || frm.doc.comm_breakup.length === 0)) {
            frm.add_child('comm_breakup');
            frm.refresh_field('comm_breakup');
        }
    },

    onload_post_render(frm) {
        if (frm.is_new()) {
            frm.set_value('date', frappe.datetime.get_today());
        }
    },

    agent(frm) {
        if (frm.doc.comm_breakup && frm.doc.comm_breakup.length > 0) {
            frm.clear_table('comm_breakup');
            // Re-add an initial empty row after clearing for better UX
            frm.add_child('comm_breakup'); 
            frm.refresh_field('comm_breakup');
            toggle_agent_readonly(frm);
        }
    },

    amount_usd(frm) {
        calculate_running_balance(frm);
    }
});

frappe.ui.form.on('Comm Breakup', {
    inv_no(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        toggle_agent_readonly(frm);
        
        if (row.inv_no) {
            frappe.call({
                method: "ssd_app.my_custom.doctype.comm_paid.comm_paid.get_inv_no_balance",
                args: { inv_no: row.inv_no },
                callback: (r) => {
                    const inv_balance = flt(r.message);
                    
                    // Calculate current running balance BEFORE this row's amount is added
                    const total_usd = flt(frm.doc.amount_usd, 2);
                    const allocated_other_rows = (frm.doc.comm_breakup || [])
                        .filter(d => d.name !== row.name)
                        .reduce((sum, d) => sum + flt(d.amount), 0);
                    
                    const remaining_to_allocate = total_usd - allocated_other_rows;

                    // Set amount as the minimum of the Invoice Balance or the Remaining Total
                    const auto_amount = Math.min(inv_balance, Math.max(0, remaining_to_allocate));
                    
                    frappe.model.set_value(cdt, cdn, 'amount', auto_amount);
                    calculate_running_balance(frm);
                }
            });
        }
    },

    amount(frm, cdt, cdn) {
        calculate_running_balance(frm);
    },

    comm_breakup_remove(frm) {
        calculate_running_balance(frm);
        toggle_agent_readonly(frm);
    }
});

function calculate_running_balance(frm) {
    const total_usd = flt(frm.doc.amount_usd, 2);
    let current_allocated = 0;

    (frm.doc.comm_breakup || []).forEach(row => {
        current_allocated += flt(row.amount);
        row.balance = total_usd - current_allocated; // Shows remaining after this row
    });

    const remaining = total_usd - current_allocated;
    
    // UI Feedback: Set a description or indicator
    if (remaining !== 0) {
        // frm.set_intro(__("Remaining to allocate: {0}", [format_currency(remaining, "USD")]), 'orange');
        frm.disable_save();
    } else {
        // frm.set_intro(__("Fully Allocated"), 'blue');
        frm.fields_dict.comm_breakup.grid.cannot_add_rows = true
        frm.enable_save();
    }

    frm.refresh_field('comm_breakup');

}

function toggle_agent_readonly(frm) {
    const has_rows = (frm.doc.comm_breakup || []).some(row => row.inv_no);
    frm.set_df_property('agent', 'read_only', has_rows ? 1 : 0);
}