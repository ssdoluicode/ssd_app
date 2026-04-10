frappe.pages['banking-line-dashboad'].on_page_load = function(wrapper) {
// frappe.pages['sales-dashboard'].on_page_load = function (wrapper) {

    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Banking Line Dashboard",
        single_column: true
    });

    page.main.html(
        frappe.render_template("banking_line_dashboad")
    );

    let charts = {};
    let current_dashboard_data = [];

    // =====================================================
    // LOAD MONTH SUMMARY
    // =====================================================
    function load_month_summary() {

        frappe.call({
            method:
                "ssd_app.my_custom.page.banking_line_dashboad.banking_line_dashboad.get_month_summary",
            freeze: true,

            callback: r => {

                let data = r.message || [];

                render_monthly_cubes(data);
                if (data.length) {
                    load_month_details(
                        data[0].month,
                        data[0].period_type
                    );
                }
            }
        });
    }

    // =====================================================
    // LOAD DETAILS
    // =====================================================
    function load_month_details(month, period_type) {

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

            args = { year: month.split("-")[1] };
        }

        frappe.call({
            method:
                "ssd_app.my_custom.page.banking_line_dashboad.banking_line_dashboad.get_data",
            args,
            freeze: true,

            callback: r => {

                current_dashboard_data = r.message || [];

                render_selected_analysis(
                    current_dashboard_data,
                    default_group
                );
            }
        });
    }

    // =====================================================
    // MONTH CARDS
    // =====================================================
    function render_monthly_cubes(data) {

        let html = "";

        data.forEach((r, i) => {

            let sales = flt(r.sales);
            let sales_nc = flt(r.sales_nc);
            let profit = sales - flt(r.cost);

            let pct = sales
                ? ((profit / sales) * 100).toFixed(2)
                : 0;

            let sales_nc_html = "";

            if (sales_nc) {

                sales_nc_html += `
                <div class="cube-row">
                    <div>Sales(Cost Pen..)</div>
                    <div>${format_number(sales_nc)}</div>
                </div>`;
            }

            html += `
                <div class="cube-card ${i === 0 ? 'active-cube' : ''}"
                    data-month="${r.month}"
                    data-period_type="${r.period_type}">

                    <div class="cube-month">${r.month}</div>

                    <div class="cube-row">
                        <div>Sales</div>
                        <div>${format_number(sales)}</div>
                    </div>

                    ${sales_nc_html}

                    <div class="cube-row">
                        <div>Gross Profit</div>
                        <div class="${profit >= 0 ? 'margin-good':'margin-bad'}">
                            ${format_number(profit)}
                            <span class="profit-pct">(${pct}%)</span>
                        </div>
                    </div>

                </div>`;
        });

        $(".monthly-cubes").html(html);

        $(".cube-card").on("click", function () {

            $(".cube-card").removeClass("active-cube");
            $(this).addClass("active-cube");
            load_month_details(
                $(this).data("month"),
                $(this).data("period_type")
            );
        });
    }

    // =====================================================
    // ANALYSIS AREA
    // =====================================================
    function render_selected_analysis(data, default_group) {

        const CONFIG = [
            { id: "customer", title: "Customer Wise" },
            { id: "notify", title: "Notify Wise" },
            { id: "company", title: "Company Wise" },
            { id: "country", title: "Country Wise" }
        ];

        let cards = CONFIG.map(c => `
            <div class="pie-card">
                <h5>${c.title}</h5>
                <div id="pie-${c.id}"></div>
            </div>
        `).join("");

        $(".analysis-content").html(`

            <div class="analysis-filters mb-3" style="display:flex; gap:10px;">

                <select id="group-by-select"
                        class="form-control"
                        style="width:200px;">
                    <option>Category</option>
                    <option>Customer</option>
                    <option>Notify</option>
                    <option>Month</option>
                </select>

                <select id="based_on"
                        class="form-control"
                        style="width:200px;">
                    <option>Sales</option>
                    <option>Gross Profit</option>
                    <option>Finance Cost</option>
                </select>

            </div>

            <div class="pie-inline-wrapper">${cards}</div>

            <div class="chart-row mt-4">

                <div class="bar-card">
                    <h5>Sales</h5>
                    <div id="chart-sales"></div>
                </div>

                <div class="bar-card">
                    <h5>Gross Profit</h5>
                    <div id="chart-g-profit"></div>
                </div>

                <div class="bar-card">
                    <h5>Finance Cost</h5>
                    <div id="chart-f-cost"></div>
                </div>

            </div>
        `);

        $("#group-by-select").val(default_group);

        let based_on = $("#based_on").val();

        CONFIG.forEach(c => {
            render_summary_table(`pie-${c.id}`, data, c.id, based_on);
        });

        $(document).on("change", "#based_on", function(){

            let based_on = $(this).val();

            CONFIG.forEach(c => {
                render_summary_table(`pie-${c.id}`, data, c.id, based_on);
            });

        });

        update_charts();
    }

    // =====================================================
    // UPDATE CHARTS
    // =====================================================
    function update_charts() {

        let map = {
            Category: "category",
            Customer: "customer",
            Notify: "notify",
            Month: "month"
        };

        let field = map[$("#group-by-select").val()];

        let metrics = ["sales","g-profit","f-cost"];

        metrics.forEach(metric => {
            render_chart(current_dashboard_data, field, metric);
        });
    }

    // =====================================================
    // RENDER CHART
    // =====================================================
    function render_chart(data, field, metric="sales") {

        let g = group_by_field(data, field);

        let rows = Object.keys(g).map(k => {

            let sales  = g[k].sales  || 0;
            let g_profit = g[k].g_profit || 0;
            let f_cost = g[k].f_cost || 0;

            let value = 0;

            if (metric === "sales")  value = sales;
            if (metric === "g-profit")   value = g_profit;
            if (metric === "f-cost") value = f_cost;

            return {
                label: k,
                value: Math.round(value)
            };
        });

        rows.sort((a, b) => {

            let A = Number(a.label);
            let B = Number(b.label);

            if (!isNaN(A) && !isNaN(B)) {
                return A - B;
            }

            return String(a.label).localeCompare(String(b.label));
        });

        let labels = rows.map(r => r.label);
        let values = rows.map(r => r.value);

        let chart_id = `#chart-${metric}`;

        if (charts[metric]) charts[metric].destroy();
        let color = "#2563eb";   // default

        if (metric === "sales")  color = "#2563eb";
        if (metric === "g-profit")   color = "#16a34a";
        if (metric === "f-cost") color =  "#f97316";

    

        charts[metric] = new frappe.Chart(chart_id, {

            data:{
                labels,
                datasets:[
                    {
                        name: metric.charAt(0).toUpperCase()+metric.slice(1),
                        values
                    }
                ]
            },

            type:"bar",

            colors:[color],

            axisOptions:{
                shortenYAxisNumbers: true,
                yAxis:{
                    numberFormatter: v => format_km(v)
                }
            },

            tooltipOptions:{
                formatTooltipY:v => v ? format_km(v) : ""
            }
        });
    }

    $(document).on(
        "change",
        "#group-by-select",
        update_charts
    );

    load_month_summary();
};


/* =====================================================
   HELPERS
===================================================== */

function group_by_field(data, field){

    let map={};

    data.forEach(r=>{

        let key=r[field]||"Unknown";

        if(!map[key])
            map[key]={sales:0,g_profit:0, f_cost:0};

        map[key].sales+=flt(r.total_sales);
        map[key].g_profit+=flt(r.total_g_profit);
        map[key].f_cost+=flt(r.total_f_cost);
    });

    return map;
}

function format_number(n){

    return Math.round(Number(n)||0)
        .toLocaleString("en-US");
}

function format_km(v){

    v = Number(v) || 0;

    if (Math.abs(v) >= 1000000)
        return (v/1000000).toFixed(1) + "M";

    if (Math.abs(v) >= 1000)
        return (v/1000).toFixed(1) + "K";

    return Math.round(v);
}


/* =====================================================
   SUMMARY TABLE
===================================================== */

function render_summary_table(id,data,field,based_on){

    let field_map = {
        "Sales": "total_sales",
        "Gross Profit": "total_g_profit",
        "Finance Cost": "total_f_cost"
    };

    let value_field = field_map[based_on] || "total_sales";

    let map={},total=0;

    data.forEach(r=>{

        let k=r[field]||"Unknown";

        let v = flt(r[value_field]) || 0;

        total+=v;

        map[k]=(map[k]||0)+v;
    });

    let rows = Object.keys(map)
        .sort((a,b)=>map[b]-map[a])
        .slice(0,10)
        .map(k=>{

            let amt=Math.round(map[k]);

            let pct=((amt/total)*100).toFixed(2);

            return `
                <div class="mini-row">
                    <div class="mini-name">${k}</div>
                    <div class="mini-right">
                        <div class="mini-amount">
                            ${amt.toLocaleString("en-US")}
                        </div>
                        <div class="mini-badge">${pct}%</div>
                    </div>
                </div>`;
        }).join("");

    $("#" + id).html(
        `<div class="mini-table">${rows}</div>`
    );
}