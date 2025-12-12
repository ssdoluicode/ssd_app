// Copyright (c) 2025, SSDolui and contributors
// For license information, please see license.txt

frappe.ui.form.on("Import Loan Payment", {
	after_save(frm) {
        // Redirect to your report page "Import Banking"
         window.location.href = "/app/query-report/Import Banking ";
    }
});
