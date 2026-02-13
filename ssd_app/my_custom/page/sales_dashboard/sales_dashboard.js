frappe.pages['sales-dashboard'].on_page_load = function(wrapper) {

    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Sales Intelligence Dashboard',
        single_column: true
    });

    $(wrapper).find(".layout-main-section")
        .html(frappe.render_template("sales_dashboard"));

    // ---------------- FILTERS ----------------
    page.add_field({
        fieldname: "from_date",
        label: "From Date",
        fieldtype: "Date",
        change: () => load_data()
    });

    page.add_field({
        fieldname: "to_date",
        label: "To Date",
        fieldtype: "Date",
        change: () => load_data()
    });

    function get_filters() {
        return {
            from_date: page.fields_dict.from_date.get_value(),
            to_date: page.fields_dict.to_date.get_value()
        };
    }

    // ---------------- MAIN LOAD ----------------
    function load_data() {

        frappe.call({
            method: "ssd_app.my_custom.page.sales_dashboard.sales_dashboard.get_dashboard_data",
            args: {
                filters: get_filters()
            },
            freeze: true,
            callback: function(r) {

                let data = r.message || {};

                render_kpi(data.kpi || {});
                render_trend(data.trend || []);
                render_trend_1(data.trend_1 || []);
                render_customers(data.top_customers || []);
                render_aging(data.aging || []);
            }
        });
    }

    // ---------------- KPI ----------------
    function render_kpi(kpi) {

        let html = `
        <div class="row">
            ${card("Total Sales", kpi.total_sales, "blue")}
            ${card("Collection", kpi.total_collection, "green")}
            ${card("Outstanding", kpi.outstanding, "red")}
            ${card("Avg Invoice", kpi.avg_invoice, "orange")}
        </div>`;

        $(".kpi-container").html(html);
    }

    function card(title, value, color) {
        return `
        <div class="col-md-3">
            <div class="kpi-card ${color}">
                <h6>${title}</h6>
                <h3>${format_currency(value || 0)}</h3>
            </div>
        </div>`;
    }

    // ---------------- LINE TREND ----------------
    function render_trend(data) {

        $("#sales-trend").empty();

        new frappe.Chart("#sales-trend", {
            data: {
                labels: data.map(d => d.month),
                datasets: [{
                    values: data.map(d => d.total)
                }]
            },
            type: "line",
            height: 280
        });
    }

    // ---------------- SALES + PROFIT BAR ----------------
    function render_trend_1(data) {

		$("#sales-profit-trend").empty();

		new frappe.Chart("#sales-profit-trend", {

			data: {
				labels: data.map(d => d.month),
				datasets: [
					{
						name: "Sales",
						values: data.map(d => (d.sales || 0) - (d.profit || 0))
					},
					{
						name: "Profit",
						values: data.map(d => d.profit || 0)
					}
				]
			},

			type: "bar",
			height: 300,

			barOptions: {
				stacked: true
			},

			axisOptions: {
				xAxisMode: "tick",
				yAxisMode: "tick",
				xIsSeries: true
			},

			// ⭐ FIX LEFT SCALE
			format: (value) => {
				return frappe.format(value, {
					fieldtype: "Currency"
				});
			},

			tooltipOptions: {
				formatTooltipY: d =>
					frappe.format(d, { fieldtype: "Currency" })
			},

			colors: ["#facc15", "#16a34a"]
		});
	}


    // ---------------- CUSTOMERS TABLE ----------------
    function render_customers(data) {

        let html = `<table class="table table-bordered table-hover">
            <thead>
                <tr>
                    <th>Customer</th>
                    <th>Total</th>
                    <th>Outstanding</th>
                </tr>
            </thead><tbody>`;

        data.forEach(row => {
            html += `
                <tr>
                    <td>${row.customer || ""}</td>
                    <td>${format_currency(row.total || 0)}</td>
                    <td>${format_currency(row.outstanding || 0)}</td>
                </tr>`;
        });

        html += "</tbody></table>";

        $("#top-customers").html(html);
    }

    // ---------------- AGING CHART ----------------
    function render_aging(data) {

        $("#aging-chart").empty();

        new frappe.Chart("#aging-chart", {
            data: {
                labels: data.map(d => d.bucket),
                datasets: [{
                    values: data.map(d => d.total)
                }]
            },
            type: "percentage",
            height: 250
        });
    }

    // first load
    load_data();
};
