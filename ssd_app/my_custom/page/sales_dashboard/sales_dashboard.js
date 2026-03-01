frappe.pages['sales-dashboard'].on_page_load = function (wrapper) {

    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Sales Dashboard",
        single_column: true
    });

    page.main.html(
        frappe.render_template("sales_dashboard")
    );

    let category_chart = null;
    let profit_chart = null;
    let current_dashboard_data = [];

    // =====================================================
    // LOAD MONTH SUMMARY
    // =====================================================
    function load_month_summary() {

        frappe.call({
            method:
                "ssd_app.my_custom.page.sales_dashboard.sales_dashboard.get_month_summary",
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
                "ssd_app.my_custom.page.sales_dashboard.sales_dashboard.get_data",
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
            let profit = sales - flt(r.cost);

            let pct = sales
                ? ((profit / sales) * 100).toFixed(2)
                : 0;

            html += `
                <div class="cube-card ${i === 0 ? 'active-cube' : ''}"
                    data-month="${r.month}"
                    data-period_type="${r.period_type}">

                    <div class="cube-month">${r.month}</div>

                    <div class="cube-row">
                        <div>Sales</div>
                        <div>${format_number(sales)}</div>
                    </div>

                    <div class="cube-row">
                        <div>Profit</div>
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
                <h6>${c.title}</h6>
                <div id="pie-${c.id}"></div>
            </div>
        `).join("");

        $(".analysis-content").html(`
            <div class="pie-inline-wrapper">${cards}</div>

            <div class="analysis-filters mb-3">
                <select id="group-by-select"
                        class="form-control"
                        style="width:200px;">
                    <option>Category</option>
                    <option>Customer</option>
                    <option>Notify</option>
                    <option>Month</option>
                </select>
            </div>

            <div class="chart-row mt-4">

                <div class="bar-card">
                    <h6>Cost vs Profit</h6>
                    <div id="sales-category-chart"></div>
                </div>

                <div class="bar-card">
                    <h6>Profit Analysis</h6>
                    <div id="profit-category-chart"></div>
                </div>

            </div>
        `);

        $("#group-by-select").val(default_group);

        CONFIG.forEach(c => {
            render_summary_table(`pie-${c.id}`, data, c.id);
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

        render_cost_profit_chart(current_dashboard_data, field);
        render_profit_chart(current_dashboard_data, field);
    }

    // =====================================================
    // COST VS PROFIT CHART
    // =====================================================
    function render_cost_profit_chart(data, field) {

        let g = group_by_field(data, field);

        let labels=[], cost=[], profit=[];

        Object.keys(g).forEach(k=>{
            labels.push(k);
            cost.push(Math.round(g[k].sales - g[k].profit));
            profit.push(Math.round(g[k].profit));
        });

        if(category_chart) category_chart.destroy();

        category_chart = new frappe.Chart(
            "#sales-category-chart",
            {
                data:{
                    labels,
                    datasets:[
                        {name:"Cost",values:cost},
                        {name:"Profit",values:profit}
                    ]
                },
                type:"bar",
                barOptions:{stacked:true},
                colors:["#f97316","#16a34a"],

                axisOptions:{
                    numberFormatter:v =>
                        Math.round(v).toLocaleString("en-US")
                },

                tooltipOptions:{
                    formatTooltipY:v =>
                        Math.round(v).toLocaleString("en-US")
                }
            }
        );
    }

    // =====================================================
    // PROFIT CHART
    // =====================================================
    function render_profit_chart(data, field){

        let g = group_by_field(data, field);

        let labels=[], values=[];

        Object.keys(g).forEach(k=>{
            labels.push(k);
            values.push(Math.round(g[k].profit));
        });

        if(profit_chart) profit_chart.destroy();

        profit_chart = new frappe.Chart(
            "#profit-category-chart",
            {
                data:{
                    labels,
                    datasets:[
                        {name:"Profit",values}
                    ]
                },
                type:"bar",
                colors:["#16a34a"],

                axisOptions:{
                    numberFormatter:v =>
                        Math.round(v).toLocaleString("en-US")
                }
            }
        );
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
            map[key]={sales:0,profit:0};

        map[key].sales+=flt(r.total_sales);
        map[key].profit+=flt(r.total_profit);
    });

    return map;
}

function format_number(n){
    return Math.round(Number(n)||0)
        .toLocaleString("en-US");
}


/* =====================================================
   SUMMARY TABLE
===================================================== */

function render_summary_table(id,data,field){

    let map={},total=0;

    data.forEach(r=>{
        let k=r[field]||"Unknown";
        let v=flt(r.total_sales)||0;
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