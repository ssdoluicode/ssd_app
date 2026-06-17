// Copyright (c) 2026, SSDolui and contributors
// For license information, please see license.txt

// FAST & RELIABLE: Look up data directly by its unique string group identifier name
window.updateChartWithRowData = function(rowValueString) {
    const report = frappe.query_report;
    if (!report || !report.data) return;

    // Direct O(1) hash map behavior: Find the active dictionary object from report memory
    const activeRow = report.data.find(r => r[report.columns[0].fieldname] === rowValueString);
    if (!activeRow) return;

    const columns = report.columns;
    const first_column_fieldname = columns[0].fieldname;
    
    let labels = [];
    let rowValues = [];
    
    // Construct single-row baseline metrics timeline array
    for (let i = 1; i < columns.length; i++) {
        const col = columns[i];
        if (col.fieldname !== "GRAND_TOTAL") {
            labels.push(col.label);
            rowValues.push(parseFloat(activeRow[col.fieldname]) || 0);
        }
    }

    report.render_chart({
        data: {
            labels: labels,
            datasets: [{ name: activeRow[first_column_fieldname], values: rowValues }]
        },
        type: "bar",
        colors: ["#765eff"]
    });
};

frappe.query_reports["Dynamic Sales Report"] = {
    onload: function(report) {
        frappe.call({
            method: "ssd_app.my_custom.report.dynamic_sales_report.dynamic_sales_report.get_first_jan_of_max_year",
            callback: function(r) {
                if (r.message) {
                    const f = report.get_filter("from_date");
                    f.df.default = r.message;
                    f.set_input(r.message);
                }
            }
        });
    },
    
    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (!data) return value;

        const columns = frappe.query_report.columns;
        const first_column_fieldname = columns[0].fieldname;

        // =====================================================
        // STYLING RULES FOR THE FINAL SUMMARY "TOTAL" ROW
        // =====================================================
        if (data[first_column_fieldname] === "Total") {
            if (column.fieldname === first_column_fieldname) {
                return `<span style="font-weight: bold; color: #1f2937; letter-spacing: 0.5px;">${value}</span>`;
            }
            return `<span style="font-weight: bold; color: #111827;">${value}</span>`;
        }

        // =====================================================
        // CASE A: CLICK 1ST COLUMN -> UPDATE THE CHART DYNAMICALLY
        // =====================================================
        if (column.fieldname === first_column_fieldname) {
            // Clean single quotes to prevent template syntax breaks on values like "Customer's Name"
            const escaped_value = String(data[first_column_fieldname]).replace(/'/g, "\\'");

            return `<a href="#"  onclick="window.updateChartWithRowData('${escaped_value}'); return false;">${value}</a>`;
        }
        
        // =====================================================
        // CASE B: CLICK MID-GRID VALUES -> DRILL DOWN WINDOW
        // =====================================================
        const field_value = data[column.fieldname];
        if (
            column.fieldname !== "GRAND_TOTAL" &&
            field_value !== 0 &&
            field_value !== undefined
        ) {
            const group_by = columns[0].label; 
            const selected_row = data[first_column_fieldname] || ""; 
            const selected_column = column.label; 
            
            const escaped_row = String(selected_row).replace(/'/g, "\\'");

            return `<a href="#" onclick="showInvWise('${group_by}', '${escaped_row}', '${selected_column}'); return false;">${value}</a>`;
        }
         
        return value;
    },

    "filters": [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "group_by",
            "label": __("Group By"),
            "fieldtype": "Select",
            "options": "\nCategory\nCustomer\nNotify\nCompany\nFrom Country\nTo Country",
            "default": "Category",
            "reqd": 1
        },
        {
            "fieldname": "column",
            "label": __("Column"),
            "fieldtype": "Select",
            "options": "\nMonthly\nQuarterly\nYearly",
            "default": "Monthly",
            "reqd": 1
        },
        {
            "fieldname": "value",
            "label": __("Value"),
            "fieldtype": "Select",
            "options": [
                { "value": "sales", "label": __("Sales") },
                { "value": "purchase", "label": __("Purchase") },
                { "value": "cost", "label": __("Cost") },
                { "value": "freight", "label": __("Freight") },
                { "value": "local_exp", "label": __("Local Expenses") },
                { "value": "comm", "label": __("Commission") },
                { "value": "profit", "label": __("Profit") },
                { "value": "profit_pct", "label": __("Profit %") }
            ],
            "default": "sales",
            "reqd": 1
        }
    ]
};

// 🧾 Modal Dialog to Show Document Flow
function showInvWise(group_by, head, period) {
    frappe.call({
        method: "ssd_app.my_custom.report.dynamic_sales_report.dynamic_sales_report.show_inv_wise",
        args: { group_by, head, period },
        callback: function (r) {
            if (r.message) {
                const d = new frappe.ui.Dialog({
                    title: `Invoice Details of: ${group_by}: ${head}, ${period}`,
                    size: 'extra-large',
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'details_html',
                            options: `
                                <div id="cif-details-a4" style="box-shadow: 0 0 8px rgba(0,0,0,0.2); max-height: 70vh; overflow-y: auto; padding: 10px;">
                                    ${r.message}
                                </div>`
                        }
                    ]
                });
                d.show();
            }
        }
    });
}