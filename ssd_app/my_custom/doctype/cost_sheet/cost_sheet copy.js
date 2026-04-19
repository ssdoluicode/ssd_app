// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

// Utility: Toggle SC No field
function toggle_po_no_field(frm) {
    const hidden = !!frm.doc.multiple_po;
    frm.toggle_display('po_no', !hidden);
    frm.toggle_reqd('po_no', !hidden);
    if (hidden) frm.set_value('po_no', '');

    const grid = frm.fields_dict.product_details.grid;
    grid.update_docfield_property('po_no', 'reqd', hidden);
    grid.update_docfield_property('po_no', 'read_only', !hidden);
}

// Utility: Toggle Supplier No field
function toggle_supplier_field(frm) {
    const hidden = !!frm.doc.multiple_supplier;
    frm.toggle_display('supplier', !hidden);
    frm.toggle_reqd('supplier', !hidden);
    if (hidden) frm.set_value('supplier', '');

    const grid = frm.fields_dict.product_details.grid;
    grid.update_docfield_property('supplier', 'reqd', hidden);
    grid.update_docfield_property('supplier', 'read_only', !hidden);
}


// Calculate total purchase
function calculate_purchase(frm) {
    const total = frm.doc.product_details.reduce((sum, row) => sum + flt(row.gross_usd), 0);
    frm.set_value('purchase', flt(total, 2));
}

function calculate_total_exp(frm) {
    return frm.doc.expenses.reduce((sum, row) => sum + flt(row.amount_usd), 0);
}

function calculate_total_qty(frm) {
    return frm.doc.product_details.reduce((sum, row) => sum + flt(row.qty), 0);
}

// Commission calculation
function calculate_commission(frm) {
    if (frm.doc.comm_based_on === "Fixed Amount"){
        frm.set_df_property('commission', 'read_only', 0);
        frm.set_value('comm_rate', 0);
        frm.set_df_property('comm_rate', 'read_only', 1);
    }else{
        frm.set_df_property('commission', 'read_only', 1);
        frm.set_df_property('comm_rate', 'read_only', 0);
        
        const rate = frm.doc.comm_rate;
        if (rate) {
            frm.toggle_reqd('agent', true);
            const base = frm.doc.comm_based_on === "Sales"
                ? flt(frm.doc.sales) * rate / 100
                : calculate_total_qty(frm) * rate;

            frm.set_value('commission', flt(base, 2));
        } else {
            frm.toggle_reqd('agent', false);
            frm.set_value('commission', 0);
        }
    }
}

// Final cost/profit calculation
function calculate_cost(frm) {
    if (!frm.doc.inv_no) return;

    frappe.db.get_value("CIF Sheet", frm.doc.inv_no, "sales")
        .then(r => {
            if (!r.message) return;

            const sales = flt(r.message.sales);
            const commission = flt(frm.doc.commission);
            const purchase = flt(frm.doc.purchase);
            const expenses = flt(calculate_total_exp(frm));

            const total_cost = flt(purchase + expenses + commission, 2);
            const profit = flt(sales - total_cost, 2);
            const profit_pct = total_cost ? flt((profit / total_cost) * 100, 2) : 0;

            frm.set_value({
                cost: total_cost,
                profit,
                profit_pct
            });
        })
        .catch(() => {
            frappe.msgprint("Failed to fetch sales value from CIF Sheet.");
        });
}



// Populate data from CIF Sheet
function get_cif_data(frm) {
    if (!frm.doc.inv_no) return;

    frappe.call({
        method: "ssd_app.my_custom.doctype.cost_sheet.cost_sheet.get_cif_data",
        args: { inv_no: frm.doc.inv_no },
        callback({ message: data }) {
            if (!data) return;

            frm.set_value({
                custom_title: data.inv_no,
                inv_date: data.inv_date,
                customer: data.customer,
                category: data.category,
                notify: data.notify,
                accounting_company: data.accounting_company,
                shipping_company: data.shipping_company,
                multiple_po: data.multiple_sc,
                po_no: data.sc_no,
                sales: data.sales
            });

            const saved_product_list = (frm.doc.product_details || []).map(row => ({
                product: row.product,
                qty: row.qty,
                unit: row.unit
            }));

            const cif_product_list = (data.product_details || []).map(row => ({
                product: row.product,
                qty: row.qty,
                unit: row.unit,
            }));
            const is_same =
            JSON.stringify(saved_product_list) ===
            JSON.stringify(cif_product_list);

            if (!is_same && !frm.is_new()){
                frm.clear_table("product_details");
                (data.product_details || []).forEach(row => {
                    frm.add_child("product_details", {
                        product: row.product,
                        qty: row.qty,
                        unit: row.unit,
                        id_code: row.name,
                        po_no: row.sc_no,
                        ...(data.handling_charges && {
                            rate: row.rate,
                            currency: row.currency,
                            ex_rate: row.ex_rate,
                            charges: row.charges,
                            charges_amount: row.charges_amount,
                            round_off_usd: row.round_off_usd
                        })
                    });
                });
            }
        

            if (frm.is_new()){
                frm.clear_table("product_details");
                (data.product_details || []).forEach(row => {
                    frm.add_child("product_details", {
                        product: row.product,
                        qty: row.qty,
                        unit: row.unit,
                        id_code: row.name,
                        po_no: row.sc_no,
                        ...(data.handling_charges && {
                            rate: row.rate,
                            currency: row.currency,
                            ex_rate: row.ex_rate,
                            charges: row.charges,
                            charges_amount: row.charges_amount,
                            round_off_usd: row.round_off_usd
                        })
                    });
                run_all_calculations(frm);
                });

                frm.clear_table("expenses");
                (data.expenses || []).forEach(row => {
                    if (data.handling_charges) {
                        frm.add_child("expenses", {
                            expenses: row.expenses,
                            amount: row.amount,
                            currency: row.currency,
                            ex_rate: row.ex_rate
                        });
                    }
                });
                
                if (data.insurance) {
                    frm.add_child("expenses", {
                        expenses: "Insurance",
                        amount: data.insurance,
                        currency: "USD",
                        ex_rate: 1
                    });
                }
            }
            frm.refresh_fields();
            run_all_calculations(frm);
           
        }
        
    });  
}



// Custom filter
function inv_no_filter(frm) {
    frm.set_query('inv_no', () => ({
        query: 'ssd_app.my_custom.doctype.cost_sheet.cost_sheet.get_available_inv_no'
    }));
}


//  Create Custom Print button
function custom_print(frm){
    frm.add_custom_button("Custom Print", function() {
        showCostDetails(frm.doc.inv_no, frm.doc.custom_title);
    });
}

function protect_add_detete_row(frm){
    let grid = frm.fields_dict.product_details.grid;
        // 1. Stop adding new rows
        grid.cannot_add_rows = true;
        // 2. Stop deleting rows (removes the trash icon/delete button)
        grid.wrapper.find('.grid-remove-rows').hide(); // Hides the "Delete" button
        grid.wrapper.find('.grid-delete-row').hide(); // Hides individual trash icons
        // grid.wrapper.find('.sortable-handle').hide();
        grid.refresh();
}



// Check duplicates on validation
function checkDuplicateExpensesOnValidation(frm) {
    let table = frm.doc.expenses || [];
    let expenses_values = table.map(r => r.expenses).filter(Boolean);

    let unique_values = new Set(expenses_values);

    if (expenses_values.length !== unique_values.size) {
        frappe.throw(__('Expenses must be uniquePPP.'));
    }
}


// --- SAFE CALCULATION ENGINE (Bypasses Event Loops) ---

function update_row_logic(frm, cdt, cdn, source_field) {
    let row = locals[cdt][cdn];
    
    // Using 4 decimal precision for internal math
    if (source_field === 'gross') {
        // User touched Gross: Calculate Rate only
        if (flt(row.qty) > 0) {
            let rate = (flt(row.gross) - flt(row.charges_amount)) / flt(row.qty);
            row.rate = flt(rate, 4); 
        }
    } else if (['rate', 'qty', 'charges_amount'].includes(source_field)) {
        // User touched Rate/Qty/Charges: Calculate Gross
        let gross = (flt(row.qty) * flt(row.rate)) + flt(row.charges_amount);
        row.gross = flt(gross, 4);
    }

    // Common USD calculation
    if (flt(row.ex_rate) > 0) {
        let usd = (flt(row.gross) / flt(row.ex_rate)) + flt(row.round_off_usd);
        row.gross_usd = flt(usd, 2); 
    }

    // Update UI without re-triggering 'on_change' events
    frm.refresh_field('product_details');
    calculate_purchase(frm);
    calculate_commission(frm);
    calculate_cost(frm);
}

function run_all_calculations(frm) {
    (frm.doc.product_details || []).forEach(row => {
        let gross = (flt(row.qty) * flt(row.rate)) + flt(row.charges_amount);
        row.gross = flt(gross, 4);
        if (flt(row.ex_rate) > 0) {
            row.gross_usd = flt((flt(row.gross) / flt(row.ex_rate)) + flt(row.round_off_usd), 2);
        }
    });
    (frm.doc.expenses || []).forEach(row => {
        if (flt(row.ex_rate) > 0) row.amount_usd = flt(row.amount / row.ex_rate, 2);
    });
    frm.refresh_fields();
    calculate_purchase(frm);
    calculate_commission(frm);
    calculate_cost(frm);
}

// Hooks
frappe.ui.form.on("Cost Sheet", {
    onload(frm){
        get_cif_data(frm);
    },
    // onload: (frm) => get_cif_data(frm),
    setup: inv_no_filter,
    inv_no: get_cif_data,
    refresh(frm) {
        toggle_po_no_field(frm);
        toggle_supplier_field(frm);
        custom_print(frm);
        protect_add_detete_row(frm);
        
        // let grid = frm.fields_dict.product_details.grid;
        // grid.cannot_add_rows = true;
        // grid.wrapper.find('.grid-remove-rows, .grid-delete-row').hide();
        // grid.refresh();
    },
    multiple_po: toggle_po_no_field,
    multiple_supplier: toggle_supplier_field,
    comm_rate: (frm) => { calculate_commission(frm); calculate_cost(frm); },
    comm_based_on: (frm) => { calculate_commission(frm); calculate_cost(frm); },
    commission(frm) {   // ✅ FIXED
        calculate_cost(frm);
    },
    validate(frm){
        checkDuplicateExpensesOnValidation(frm);
    },
    after_save(frm) {
        showCostDetails(frm.doc.inv_no, frm.doc.custom_title);
    }
});

frappe.ui.form.on("Product Cost", {
    rate: (frm, cdt, cdn) => update_row_logic(frm, cdt, cdn, 'rate'),
    qty: (frm, cdt, cdn) => update_row_logic(frm, cdt, cdn, 'qty'),
    charges_amount: (frm, cdt, cdn) => update_row_logic(frm, cdt, cdn, 'charges_amount'),
    gross: (frm, cdt, cdn) => update_row_logic(frm, cdt, cdn, 'gross'),
    ex_rate: (frm, cdt, cdn) => update_row_logic(frm, cdt, cdn, 'ex_rate'),
    round_off_usd: (frm, cdt, cdn) => update_row_logic(frm, cdt, cdn, 'round_off_usd')
});

frappe.ui.form.on("Expenses Cost", {
    amount: (frm, cdt, cdn) => {
        let row = locals[cdt][cdn];
        if (flt(row.ex_rate) > 0) row.amount_usd = flt(row.amount / row.ex_rate, 2);
        frm.refresh_field('expenses');
        calculate_cost(frm);
    },
    ex_rate: (frm, cdt, cdn) => {
        let row = locals[cdt][cdn];
        if (flt(row.ex_rate) > 0) row.amount_usd = flt(row.amount / row.ex_rate, 2);
        frm.refresh_field('expenses');
        calculate_cost(frm);
    },
    expenses: (frm, cdt, cdn) => {
        let row = locals[cdt][cdn];
        if ((frm.doc.expenses || []).some(r => r.name !== row.name && r.expenses === row.expenses)) {
            frappe.msgprint('Expenses must be unique.');
            frappe.model.set_value(cdt, cdn, 'expenses', null);
        }
    }
});
