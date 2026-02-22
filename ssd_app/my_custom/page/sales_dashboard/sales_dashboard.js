frappe.pages['sales-dashboard'].on_page_load = function (wrapper) {

    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Sales Dashboard",
        single_column: true
    });

    page.main.html(
        frappe.render_template("sales_dashboard")
    );

    let selected_month = null;
    let period_type = null;
    let category_chart = null;
    let current_dashboard_data = [];

    // ==================================================
    // Load Month Summary
    // ==================================================
    function load_month_summary() {
        frappe.call({
            method: "ssd_app.my_custom.page.sales_dashboard.sales_dashboard.get_month_summary",
            freeze: true,
            callback: function (r) {
                let data = r.message || [];
                render_monthly_cubes(data);

                if (data.length) {
                    selected_month = data[0].month;
                    period_type = data[0].period_type;
                    load_month_details(selected_month, period_type);
                }
            }
        });
    }

    // ==================================================
    // Load Month Details
    // ==================================================
    function load_month_details(month, p_type) {
        selected_month = month;
        period_type = p_type;

        let args = {};
        let default_group = "";

        if (period_type === "month") {
            default_group = "Category";
            args = {
                year: month.split("-")[0],
                month: month.split("-")[1]
            };
        } else {
            default_group = "Month";
            args = {
                year: month.split("-")[1]
            };
        }

        // $("#group-by-select").val(default_group);

        frappe.call({
            method: "ssd_app.my_custom.page.sales_dashboard.sales_dashboard.get_data",
            args: args,
            freeze: true,
            callback: function (r) {
                current_dashboard_data = r.message || [];
                render_selected_analysis(current_dashboard_data, default_group); 
            }
        });
    }

    // ==================================================
    // Render Month Cubes
    // ==================================================
    function render_monthly_cubes(data) {
        if (!data || !data.length) return;

        function formatMonth(monthStr) {
            let [year, month] = monthStr.split("-");
            let date = new Date(year, month - 1);
            return date.toLocaleString("en-US", { month: "short" }) 
                + "-" + year.slice(2);
        }

        let html = "";

        data.forEach((r, index) => {
            let sales = flt(r.sales);
            let sales_nc = flt(r.sales_nc);
            let cost = flt(r.cost);
            let profit = sales - cost;

            let period = r.period_type === "month"
                ? formatMonth(r.month)
                : r.month;

            let profit_pct = sales
                ? ((profit / sales) * 100).toFixed(2)
                : "0.00";

            let marginClass = profit >= 0 ? "margin-good" : "margin-bad";
            let activeClass = index === 0 ? "active-cube" : "";
            let sales_nc_html = "";
            if(sales_nc){
                sales_nc_html = `
                <div class="cube-row">
                    <div class="cube-label">Sales(Pending)</div>
                    <div class="cube-value">
                        ${format_number(sales_nc)}
                    </div>
                </div>`
            }

            html += `
                <div class="cube-card ${activeClass}" 
                    data-month="${r.month}"
                    data-period_type="${r.period_type}">
                    
                    <div class="cube-month">${period}</div>

                    <div class="cube-row">
                        <div class="cube-label">Sales</div>
                        <div class="cube-value">
                            ${format_number(sales)}
                        </div>
                    </div>
                    
                    ${sales_nc_html}

                    <div class="cube-row">
                        <div class="cube-label">Profit</div>
                        <div class="cube-value ${marginClass}">
                            ${format_number(profit)}
                            <span class="profit-pct">(${profit_pct}%)</span>
                        </div>
                    </div>
                </div>
            `;
        });

        $(".monthly-cubes").html(html);

        $(".cube-card").off("click").on("click", function () {
            $(".cube-card").removeClass("active-cube");
            $(this).addClass("active-cube");

            load_month_details(
                $(this).data("month"),
                $(this).data("period_type")
            );
        });
    }

    // ==================================================
    // Render Analysis Area
    // ==================================================
    function render_selected_analysis(data, default_group) {
        if (!data || !data.length) {
            $(".analysis-content").html("<p>No data available</p>");
            return;
        }

        let html = `
            <div class="pie-inline-wrapper">
                <div class="pie-card">
                    <h6>Customer Wise</h6>
                    <div id="pie-customer"></div>
                </div>
                <div class="pie-card">
                    <h6>Notify Party Wise</h6>
                    <div id="pie-notify"></div>
                </div>
                <div class="pie-card">
                    <h6>Company Wise</h6>
                    <div id="pie-company"></div>
                </div>
                <div class="pie-card">
                    <h6>To Country Wise</h6>
                    <div id="pie-country"></div>
                </div>
            </div>

            <div class="analysis-filters mb-3">
                    <select id="group-by-select" class="form-control" style="width:200px;">
                        <option value="Category">Category</option>
                        <option value="Customer">Customer</option>
                        <option value="Notify">Notify</option>
                        <option value="Month">Month</option>
                    </select>
                    <div id="analysis-filter-fields"></div>
                </div>

        

            <div class="bar-card mt-4">
                <h6 id="bar-title">Performance Overview</h6>
                <div id="sales-category-chart" style="height:350px;"></div>
            </div>
        `;
        $(".analysis-content").html(html);
        if (default_group) {
            $("#group-by-select").val(default_group);
        }
        
        render_pie("pie-customer", data, "customer");
        render_pie("pie-notify", data, "notify");
        render_pie("pie-company", data, "company");
        render_pie("pie-country", data, "country");

        update_bar_chart();
    }

    // ==================================================
    // Update Bar Chart
    // ==================================================
    function update_bar_chart() {
        if (!current_dashboard_data.length) return;

        let selected_group = $("#group-by-select").val();

        let group_map = {
            "Category": "category",
            "Customer": "customer",
            "Notify": "notify",
            "Month": "month"
        };

        let field = group_map[selected_group] || "category";
        $("#bar-title").text("Performance by " + selected_group);
        render_category_chart(current_dashboard_data, field);
    }

    // ==================================================
    // Render Bar Chart
    // ==================================================
    function render_category_chart1(data, field) {
        let grouped = group_by_field(data, field);

        let labels = [];
        let cost_values = [];
        let profit_values = [];
        // We create a helper array to store the percentages
        let profit_percentages = [];

        Object.keys(grouped).forEach(function (key) {
            let sales = flt(grouped[key].sales);
            let profit = flt(grouped[key].profit);
            let cost = Math.round(sales - profit);
            let display_label = key;

            if (field === "month" && key) {
                let date = key.includes("-") ? new Date(key.split("-")[0], key.split("-")[1] - 1) : new Date(key);
                if (!isNaN(date.getTime())) {
                    display_label = date.toLocaleString("en-US", { month: "short" });
                }
            }

            labels.push(display_label);
            cost_values.push(cost);
            profit_values.push(Math.round(profit));

            // Pre-calculate percentage string
            let percentage = (cost > 0) ? ((profit / cost) * 100).toFixed(2) : "0.00";
            profit_percentages.push(percentage);
        });

        if (category_chart) {
            category_chart.destroy();
        }

        category_chart = new frappe.Chart("#sales-category-chart", {
            data: {
                labels: labels,
                datasets: [
                    { name: "Cost", values: cost_values },
                    { name: "Profit", values: profit_values }
                ]
            },
            type: "bar",
            height: 350,
            barOptions: { stacked: true },
            colors: ['orange', '#2F9E44'],
            tooltipOptions: {
                // Frappe Charts' tooltip formatter often only reliable passes the value
                formatTooltipY: (value) => {
                    let num_val = parseFloat(value);
                    let formatted = num_val.toLocaleString();

                    // Logic: Check if this value exists in our profit array to append %
                    // Note: This works best if Profit and Cost values are unique-ish
                    let idx = profit_values.indexOf(num_val);
                    if (idx !== -1 && profit_percentages[idx]) {
                        return `${formatted} (${profit_percentages[idx]}%)`;
                    }
                    
                    return formatted;
                }
            }
        });
    }

    function render_category_chart(data, field) {
        let grouped = group_by_field(data, field);

        let labels = [];
        let cost_values = [];
        let profit_values = [];
        let profit_percentages = [];

        // --- SORTING LOGIC ADDED HERE ---
        // This sorts the keys (e.g., "Jan", "Feb" or "Category A", "Category B") 
        // alphabetically/numerically before processing the data.
        let sorted_keys = Object.keys(grouped);
        if ((field || "").toLowerCase() !== "month") {
            sorted_keys = Object.keys(grouped).sort();
        }

        sorted_keys.forEach(function (key) {
            let sales = flt(grouped[key].sales);
            let profit = flt(grouped[key].profit);
            let cost = Math.round(sales - profit);
            let display_label = key;

            if (field === "month" && key) {
                let date = key.includes("-") ? new Date(key.split("-")[0], key.split("-")[1] - 1) : new Date(key);
                if (!isNaN(date.getTime())) {
                    display_label = date.toLocaleString("en-US", { month: "short" });
                }
            }

            labels.push(display_label);
            cost_values.push(cost);
            profit_values.push(Math.round(profit));

            let percentage = (cost > 0) ? ((profit / cost) * 100).toFixed(2) : "0.00";
            profit_percentages.push(percentage);
        });

        if (category_chart) {
            category_chart.destroy();
        }

        category_chart = new frappe.Chart("#sales-category-chart", {
            data: {
                labels: labels,
                datasets: [
                    { name: "Cost", values: cost_values },
                    { name: "Profit", values: profit_values }
                ]
            },
            type: "bar",
            height: 350,
            barOptions: { stacked: true },
            colors: ['orange', '#2F9E44'],
            tooltipOptions: {
                formatTooltipY: (value) => {
                    let num_val = parseFloat(value);
                    let formatted = num_val.toLocaleString();

                    let idx = profit_values.indexOf(num_val);
                    if (idx !== -1 && profit_percentages[idx]) {
                        return `${formatted} (${profit_percentages[idx]}%)`;
                    }
                    
                    return formatted;
                }
            }
        });
    }


    $(document).on("change", "#group-by-select", function () {
        update_bar_chart();
    });

    load_month_summary();
};

// ==================================================
// Pie Chart (Updated with formatted tooltips)
// ==================================================
function render_pie(id, data, field) {
    let map = {};
    let total = 0;

    data.forEach(function (row) {
        let key = row[field] || "Unknown";
        let val = flt(row.total_sales) || 0;
        total += val;
        map[key] = (map[key] || 0) + val;
    });

    let sorted = Object.keys(map)
        .map(k => ({ name: k, value: map[k] }))
        .sort((a, b) => b.value - a.value);

    let top10 = sorted.slice(0, 10);
    let others = sorted.slice(10);
    let othersTotal = others.reduce((sum, x) => sum + x.value, 0);

    if (othersTotal > 0) {
        top10.push({ name: "Others", value: othersTotal });
    }

    let labels = top10.map(x => x.name);
    let values = top10.map(x => Math.round(x.value));

    const chart_colors = ["#4C6EF5", "#1098AD", "#F08C00", "#C2255C", "#5F3DC4", "#2B8A3E", "#E03131", "#0CA678", "#1C7ED6", "#F76707", "#bbbdbf"];

    new frappe.Chart("#" + id, {
        data: {
            labels: labels,
            datasets: [{ values: values }]
        },
        type: "pie",
        height: 280,
        colors: chart_colors,
        tooltipOptions: {
            formatTooltipY: function (value) {
                // Update: Round to 0 and add comma separator
                let amount = Math.round(value);
                let formatted_amount = amount.toLocaleString("en-IN");
                let percent = total ? ((amount / total) * 100).toFixed(2) : "0.00";

                return formatted_amount + " (" + percent + "%)";
            }
        }
    });
}

// ==================================================
// Group Helper
// ==================================================
function group_by_field(data, field) {
    let map = {};
    data.forEach(function (row) {
        let key = row[field] || "Unknown";
        let sales = flt(row.total_sales) || 0;
        let profit = flt(row.total_profit) || 0;

        if (!map[key]) {
            map[key] = { sales: 0, profit: 0 };
        }
        map[key].sales += sales;
        map[key].profit += profit;
    });
    return map;
}

// ==================================================
// Safe Number Formatter
// ==================================================
// function format_number(num) {
//     if (num === null || num === undefined) return "0";
//     let n = Number(num);
//     if (isNaN(n)) return "0";
//     return Math.round(n).toLocaleString("en-IN");
// }
function format_number(num) {

    if (num === null || num === undefined) return "0";

    let n = Number(num);

    if (isNaN(n)) return "0";

    return Math.round(n).toLocaleString("en-US");
}