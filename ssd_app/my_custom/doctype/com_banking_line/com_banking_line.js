// Copyright (c) 2026
// SSD App – Com Banking Line Client Script
// ---------------------------------------

var banking_utils = {

    // ---------------------------------------
    // Set dynamic query for combind_banking_line
    // ---------------------------------------
    set_query: function (frm) {
        frm.set_query(
            "combind_banking_line",
            "banking_line_details",
            function () {
                return {
                    query: "ssd_app.my_custom.doctype.com_banking_line.com_banking_line.banking_line_filter",
                    filters: {
                        bank: frm.doc.bank
                    }
                };
            }
        );
    },

    // ---------------------------------------
    // Toggle banking_line field based on individual_limit
    // ---------------------------------------
    toggle_row_fields: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row) return;

        const grid = frm.get_field("banking_line_details")?.grid;
        if (!grid) return;

        const grid_row = grid.get_row(cdn);
        if (!grid_row) return;

        const enable = (row.individual_limit == 1);

        // Editable
        grid_row.toggle_editable("banking_line", enable);

        // Mandatory
        grid_row.toggle_reqd("banking_line", enable);

        // Clear value if disabled
        if (!enable && row.banking_line) {
            frappe.model.set_value(cdt, cdn, "banking_line", null);
        }

        grid_row.refresh();
    },

    // ---------------------------------------
    // Initialize all child rows
    // ---------------------------------------
    init_child_rows: function (frm) {
        (frm.doc.banking_line_details || []).forEach(row => {
            banking_utils.toggle_row_fields(frm, row.doctype, row.name);
        });
    },

    // ---------------------------------------
    // VALIDATION (SAVE BLOCKING)
    // individual_limit = 1 → banking_line must be > 0
    // ---------------------------------------
    validate_banking_line: function (frm) {

        // 🔑 CRITICAL: sync grid → frm.doc
        frm.refresh_field("banking_line_details");

        let invalid_rows = [];

        (frm.doc.banking_line_details || []).forEach((row, idx) => {
            
            if (row.individual_limit == 1) {
                if (!row.banking_line || flt(row.banking_line) <= 0) {
                    invalid_rows.push(idx + 1);
                }
            }
            
        });

        if (invalid_rows.length) {
            frappe.throw({
                title: __("Validation Error"),
                message: __(
                    "Banking Line must be greater than 0 for rows: {0}",
                    [invalid_rows.join(", ")]
                ),
                indicator: "red"
            });
        }
    }
};


// =======================================================
// Parent Doctype: Com Banking Line
// =======================================================
frappe.ui.form.on("Com Banking Line", {

    setup(frm) {
        banking_utils.set_query(frm);
    },

    refresh(frm) {
        banking_utils.init_child_rows(frm);
    },

    validate(frm) {
        banking_utils.validate_banking_line(frm);
    },

    bank(frm) {
        if (frm.doc.banking_line_details?.length) {
            frm.clear_table("banking_line_details");
            frm.add_child("banking_line_details");
            frm.refresh_field("banking_line_details");
        }
    }
});


// =======================================================
// Child Doctype: Com Banking Line Breakup
// (UI BEHAVIOR ONLY)
// =======================================================
frappe.ui.form.on("Com Banking Line Breakup", {

    individual_limit(frm, cdt, cdn) {
        banking_utils.toggle_row_fields(frm, cdt, cdn);
    },

    banking_line(frm, cdt, cdn) {
        banking_utils.toggle_row_fields(frm, cdt, cdn);
    },

    form_render(frm, cdt, cdn) {
        banking_utils.toggle_row_fields(frm, cdt, cdn);
    }
});
