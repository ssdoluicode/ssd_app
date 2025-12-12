// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.ui.form.on("Usance LC", {
	after_save: function(frm) {
        // Redirect to the report page after save
        window.location.href = "/app/query-report/Import Banking";
    }
});
