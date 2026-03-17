frappe.ui.form.on('Comm Paid', {

    refresh(frm) {

        $(frm.wrapper).off('keydown.form_focus_loop');

        $(frm.wrapper).on('keydown.form_focus_loop', function (e) {

            if (e.key !== "Tab") return;

            let focusable = $(frm.wrapper)
                .find('input, select, textarea, button')
                .filter(':visible:not([disabled])');

            if (!focusable.length) return;

            let first = focusable.first()[0];
            let last  = focusable.last()[0];

            if (e.shiftKey) {
                if (document.activeElement === first) {
                    e.preventDefault();
                    last.focus();
                }
            } else {
                if (document.activeElement === last) {
                    e.preventDefault();
                    first.focus();
                }
            }
        });
    },

    setup(frm) {
        frm.set_query('inv_no', 'comm_breakup', () => ({
            query: "ssd_app.my_custom.doctype.comm_paid.comm_paid.get_filter_inv_no",
            filters: { agent: frm.doc.agent }
        }));
    },

    onload(frm) {

        if (frm.is_new() && !(frm.doc.comm_breakup || []).length) {
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

        if ((frm.doc.comm_breakup || []).length) {

            frm.clear_table('comm_breakup');

            frm.add_child('comm_breakup');

            frm.refresh_field('comm_breakup');

            toggle_agent_readonly(frm);
        }

    },

    amount_usd: async function(frm) {
        await calculate_running_balance(frm);
    }

});


frappe.ui.form.on('Comm Breakup', {

    inv_no: async function(frm, cdt, cdn) {

        const row = locals[cdt][cdn];

        toggle_agent_readonly(frm);

        if (!row.inv_no) return;

        let r = await frappe.call({
            method: "ssd_app.my_custom.doctype.comm_paid.comm_paid.get_inv_no_balance",
            args: { inv_no: row.inv_no }
        });

        const inv_balance = flt(r.message);

        const total_usd = flt(frm.doc.amount_usd);

        const allocated_other_rows = (frm.doc.comm_breakup || [])
            .filter(d => d.name !== row.name)
            .reduce((sum, d) => sum + flt(d.amount), 0);

        const remaining = total_usd - allocated_other_rows;

        const auto_amount = Math.min(inv_balance, Math.max(0, remaining));

        await frappe.model.set_value(cdt, cdn, 'amount', auto_amount);

        await calculate_running_balance(frm);
    },

    amount: async function(frm) {
        await calculate_running_balance(frm);
    },

    comm_breakup_remove: async function(frm) {
        await calculate_running_balance(frm);
        toggle_agent_readonly(frm);
    }

});


async function calculate_running_balance(frm) {

    const total = flt(frm.doc.amount_usd);

    let allocated = 0;

    (frm.doc.comm_breakup || []).forEach(row => {

        allocated += flt(row.amount);

        row.balance = total - allocated;

    });

    const remaining = total - allocated;

    const grid = frm.fields_dict.comm_breakup.grid;

    if (remaining !== 0) {

        frm.disable_save();

        grid.cannot_add_rows = false;

    } else {

        frm.enable_save();

        grid.cannot_add_rows = true;

    }

    frm.refresh_field('comm_breakup');

}


function toggle_agent_readonly(frm) {

    const has_invoice = (frm.doc.comm_breakup || []).some(d => d.inv_no);

    frm.set_df_property('agent', 'read_only', has_invoice ? 1 : 0);

}


