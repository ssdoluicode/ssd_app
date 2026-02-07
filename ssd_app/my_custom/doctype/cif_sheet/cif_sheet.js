// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt
function inv_no_filter(frm) {
    frm.set_query('inv_no', () => ({
        query: 'ssd_app.my_custom.doctype.cif_sheet.cif_sheet.get_available_inv_no'
    }));
}

function check_unique_inv_no(frm){
    if (!frm.doc.inv_no) return;
        frappe.db.get_value('CIF Sheet', { inv_no: frm.doc.inv_no }, 'name')
        .then(r => {
            if (r && r.message && r.message.name && r.message.name !== frm.doc.name) {
                frappe.msgprint({
                    title: __(`Duplicate Entry: ${frm.doc.inv_no}`),
                    message: __('Invoice Number must be unique. This one already exists.'),
                    indicator: 'red'
                });
                frm.set_value('inv_no', '');
            }
        });
}

function get_shipping_book_data(frm) {
    if (!frm.doc.inv_no) return;

    frappe.call({
        method: "ssd_app.my_custom.doctype.cif_sheet.cif_sheet.get_shipping_book_data",
        args: { inv_no: frm.doc.inv_no },
        callback({ message: data }) {
            if (!data) return;

            frm.set_value({
                customer: data.customer,
                notify: data.notify,
                shipping_company: data.shipping_company,
                inv_date: data.bl_date,
                document: data.document,
                payment_term:data.payment_term,
                bank: data.bank,
                term_days: data.term_days,
            });
            if (frm.is_new()) {
                frm.set_value("final_destination", data.final_destination);
            }
            }
        });
    }

frappe.ui.form.on("CIF Sheet", {
    setup(frm) {
        inv_no_filter(frm);
        // Filter products by category (Standardized)
        frm.set_query("product", "product_details", () => {
            return { filters: { category: frm.doc.category || "blank" } };
        });
    },

    refresh(frm) {
        frm.trigger('handle_ui_logic');
        if (!frm.is_new()) {
            frm.add_custom_button(__("Custom Print"), () => showCIFDetails(frm.doc.name, frm.doc.inv_no));
        }
    },

    onload(frm) {
        get_shipping_book_data(frm);
        frm.trigger('calculate_all');
    },


    handle_ui_logic(frm) {
        const is_mult = !!frm.doc.multiple_sc;
        const has_product = frm.doc.product_details?.some(row => row.product);
        const has_expenses = (frm.doc.expenses || []).length > 0;

        // --- SC No Field Logic (Main Header) ---
        // If Multiple SC is checked, the header field is hidden and not required
        frm.toggle_display('sc_no', !is_mult);
        frm.toggle_reqd('sc_no', !is_mult);
        
        if (is_mult) {
            frm.set_value('sc_no', '');
        }

        // --- Child Grid Logic (Product Details Table) ---
        const grid = frm.fields_dict.product_details.grid;

        // 1. Mandatory logic: If Multiple SC is checked, sc_no in rows MUST be filled (reqd)
        grid.update_docfield_property('sc_no', 'reqd', is_mult ? 1 : 0);
        
        // 2. Read-only logic: If Multiple SC is checked, allow editing; otherwise, lock it
        grid.update_docfield_property('sc_no', 'read_only', is_mult ? 0 : 1);

        // --- Category Read Only Logic ---
        // Lock category selection if products have already been added
        frm.set_df_property('category', 'read_only', !!has_product);

        // --- Section Collapse Logic ---
        // Automatically collapse/expand the expenses section based on row count
        if (frm.fields_dict.expenses_section) {
            frm.fields_dict.expenses_section.collapse(!has_expenses);
        }

        // Ensure the grid UI updates to show the mandatory red asterisks
        frm.refresh_field('product_details');
    },

    inv_no(frm) {
        check_unique_inv_no(frm);
        get_shipping_book_data(frm);
        
    },

    inv_date(frm) {
        if (frm.doc.inv_date && !frm.doc.from_date) {
            frm.set_value("from_date", frm.doc.inv_date);
        }
    },

    // notify(frm) {
    //     if (frm.doc.notify) {
    //         frappe.db.get_value("Notify", frm.doc.notify, "city").then(r => {
    //             if (r.message) frm.set_value("final_destination", r.message.city);
    //         });
    //     }
    // },

    multiple_sc: frm => frm.trigger('handle_ui_logic'),

    document(frm) {
        frm.trigger('calculate_all');
        // frm.trigger('apply_payment_term_logic');
    },

    payment_term(frm) {
        // frm.trigger('apply_payment_term_logic');
        frm.trigger('calculate_all');
    },

    apply_payment_term_logic(frm) {
        const doc_amt = flt(frm.doc.document);
        const term = frm.doc.payment_term;

        // Document == 0 logic
        if (doc_amt === 0) {
            frm.set_value('payment_term', 'TT');
            frm.set_df_property('payment_term', 'read_only', 1);
            frm.set_df_property('bank_ref_no', 'read_only', 1);
        } else {
            frm.set_df_property('payment_term', 'read_only', 0);
            frm.set_df_property('bank_ref_no', 'read_only', 0);
        }

        // Bank lock logic
        frm.set_df_property('bank', 'read_only', term === "TT" ? 1 : 0);

        // Term days logic
        if (["TT", "DP", "LC at Sight"].includes(term)) {
            frm.set_value("term_days", 30);
            frm.set_df_property('term_days', 'read_only', 1);
        } else {
            frm.set_df_property('term_days', 'read_only', 0);
        }
    },

    // Centralized Calculation Engine
    calculate_all(frm) {
        // 1. Gross Sales
        const total_gross = (frm.doc.product_details || []).reduce((sum, d) => sum + flt(d.gross_usd), 0);
        frm.set_value('gross_sales', flt(total_gross, 2));

        // 2. Total Expenses
        const total_exp = (frm.doc.expenses || []).reduce((sum, d) => sum + flt(d.amount_usd), 0);

        // 3. Insurance

        if (frm.doc.insurance_based_on === "Fixed Amount") {
            frm.set_df_property('insurance', 'read_only', 0);
            frm.set_value('insurance_pct', null);
            frm.set_df_property('insurance_pct', 'read_only', 1);
        }else{
            let ins_base = frm.doc.insurance_based_on === "On Gross" ? total_gross : (total_gross + total_exp);
            let insurance = flt(ins_base * flt(frm.doc.insurance_pct) / 100);
            frm.set_df_property('insurance', 'read_only', 1);
            frm.set_df_property('insurance_pct', 'read_only', 0);
            frm.set_value('insurance', insurance);

        }

        // 4. Handling
        if (frm.doc.handling_based_on === "Fixed Amount") {
            frm.set_df_property('handling_charges', 'read_only', 0);
            frm.set_value('handling_pct', null);
            frm.set_df_property('handling_pct', 'read_only', 1);
        }else{
            let hand_base = frm.doc.handling_based_on === "On Gross" ? total_gross : (total_gross + total_exp + flt(frm.doc.insurance));
            let handling = flt(hand_base * flt(frm.doc.handling_pct) / 100);
            frm.set_value('handling_charges', flt(handling, 2));


        }
        // 5. Overall Sales & CC
        const total_sales = total_gross + total_exp + flt(frm.doc.insurance) + flt(frm.doc.handling_charges);
        frm.set_value('sales', flt(total_sales, 2));
        frm.set_value('cc', flt(total_sales - flt(frm.doc.document), 2));

        // 6. Due Date
        if (frm.doc.from_date && frm.doc.term_days) {
            frm.set_value('due_date', frappe.datetime.add_days(frm.doc.from_date, frm.doc.term_days));
        }
    },

    validate(frm) {
        frm.trigger('calculate_all');
        // Propagate SC No
        if (!frm.doc.multiple_sc && frm.doc.sc_no) {
            frm.doc.product_details.forEach(row => { row.sc_no = frm.doc.sc_no; });
            frm.refresh_field('product_details');
        }
        // Unique Expenses check
        let expense_types = (frm.doc.expenses || []).map(r => r.expenses).filter(Boolean);
        if (expense_types.length !== new Set(expense_types).size) {
            frappe.throw(__('Expenses must be unique.'));
        }
    },


    after_save(frm) {
        showCIFDetails(frm.doc.name, frm.doc.inv_no);
    },

    from_date: frm => frm.trigger('calculate_all'),
    term_days: frm => frm.trigger('calculate_all'),
    insurance_pct: frm => frm.trigger('calculate_all'),
    insurance_based_on: frm => frm.trigger('calculate_all'),
    insurance: frm => frm.trigger('calculate_all'),
    handling_pct: frm => frm.trigger('calculate_all'),
    handling_based_on: frm => frm.trigger('calculate_all'),
    handling_charges: frm => frm.trigger('calculate_all')
});

// Product Child Table logic
frappe.ui.form.on("Product CIF", {
    product(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frm.trigger('handle_ui_logic');
        if (row.product) {
            // Fetch Unit and check category
            frappe.db.get_value("Product", row.product, ["unit", "category"]).then(r => {
                if (r.message) {
                    if (r.message.category !== frm.doc.category) {
                        frappe.model.set_value(cdt, cdn, "product", "");
                        frappe.msgprint(__(`Product "${row.product}" is not under category ${frm.doc.category}`));
                    } else {
                        frappe.model.set_value(cdt, cdn, "unit", r.message.unit);
                    }
                }
            });
        }
    },
    rate: (frm, cdt, cdn) => update_product_row(frm, cdt, cdn),
    qty: (frm, cdt, cdn) => update_product_row(frm, cdt, cdn),
    gross: (frm, cdt, cdn) => update_product_row_rate(frm, cdt, cdn),
    charges_amount: (frm, cdt, cdn) => update_product_row(frm, cdt, cdn),
    ex_rate: (frm, cdt, cdn) => update_product_row(frm, cdt, cdn),
    round_off_usd: (frm, cdt, cdn) => update_product_row(frm, cdt, cdn),
    product_details_remove: frm => frm.trigger('calculate_all')
});

function update_product_row(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let gross = (flt(row.qty) * flt(row.rate)) + flt(row.charges_amount);
    frappe.model.set_value(cdt, cdn, "gross", gross);
    
    if (flt(row.ex_rate)>0) {
        let usd = (gross / flt(row.ex_rate)) + flt(row.round_off_usd);
        frappe.model.set_value(cdt, cdn, "gross_usd", flt(usd, 2));
    }
    frm.trigger('calculate_all');
}

function update_product_row_rate(frm, cdt, cdn) {
    let row = locals[cdt][cdn];

    // 1. Calculate Rate: (Gross - Charges) / Qty
    // Use a guard clause to prevent division by zero
    if (flt(row.qty) > 0) {
        let calculated_rate = (flt(row.gross) - flt(row.charges_amount)) / flt(row.qty);
        frappe.model.set_value(cdt, cdn, "rate", calculated_rate);
    
        // 2. Calculate USD
        // Fix: Reference flt(row.gross) instead of the undefined 'gross'
        if (flt(row.ex_rate) > 0) {
            let usd = (flt(row.gross) / flt(row.ex_rate)) + flt(row.round_off_usd);
            frappe.model.set_value(cdt, cdn, "gross_usd", flt(usd, 2));
        }

        frm.trigger('calculate_all');
    }
}


// Expenses Child Table logic
frappe.ui.form.on("Expenses CIF", {
    expenses(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let is_dup = (frm.doc.expenses || []).some(r => r.name !== row.name && r.expenses === row.expenses);
        if (is_dup) {
            frappe.msgprint(__('Expenses must be unique.'));
            frappe.model.set_value(cdt, cdn, 'expenses', null);
        }
    },
    amount: (frm, cdt, cdn) => update_expense_row(frm, cdt, cdn),
    ex_rate: (frm, cdt, cdn) => update_expense_row(frm, cdt, cdn),
    expenses_remove: frm => frm.trigger('calculate_all')
});

function update_expense_row(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (flt(row.ex_rate)) {
        frappe.model.set_value(cdt, cdn, "amount_usd", flt(flt(row.amount) / flt(row.ex_rate), 2));
    }
    frm.trigger('calculate_all');
}