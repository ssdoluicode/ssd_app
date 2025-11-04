// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt


frappe.query_reports["CC Balance"] = {

    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        // Make "customer_name" column clickable safely
        if (column.fieldname === "customer_name" && data && data.customer) {
            // Use HTML <span> with data attributes instead of raw <a> onclick
            return `<span class="open-cc-report-link"
                          data-customer="${data.customer}"
                          data-from_date="${data.from_date || frappe.query_report.get_filter_value('from_date')}"
                          data-as_on="${frappe.query_report.get_filter_value('as_on')}"
                          style="cursor:pointer;">
                        ${value}
                    </span>`;
        }

        return value;
    },

    onload: function(report) {
        // Attach click handler
        $(document).off('click', '.open-cc-report-link'); // remove previous handlers to avoid duplicates
        $(document).on('click', '.open-cc-report-link', function(e) {
            e.preventDefault();

            const customer = $(this).data('customer');
            const from_date = $(this).data('from_date');
            const as_on = $(this).data('as_on');

            // Navigate to CC Report with filters
            frappe.set_route('query-report', 'CC Report', {
                customer: customer,
                from_date: from_date,
                as_on: as_on
            });
        });
    },

    filters: [
        {
            "fieldname": "as_on",
            "label": __("As On"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        }
    ]

};
