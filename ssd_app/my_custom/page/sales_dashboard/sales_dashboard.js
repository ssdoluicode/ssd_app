frappe.pages['sales-dashboard'].on_page_load = function (wrapper) {

    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Sales Dashboard",
        single_column: true
    });

    page.main.html(
        frappe.render_template("sales_dashboard")
    );

    let charts = {};
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








    // -*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*-

    // =====================================================
    // SECONDARY DASHBOARD TAB (FILTER ROW & GRID SECTIONS)
    // =====================================================
    function initDashboardFilters() {
        // Toggle Elements for both Dropdowns
        const toggleBtnMetric = document.getElementById("dropdown-toggle-btn");
        const menuPanelMetric = document.getElementById("dropdown-menu-panel");
        const toggleBtnRow = document.getElementById("dropdown-toggle-btn-1");
        const menuPanelRow = document.getElementById("dropdown-menu-panel-1");
        
        // Structural Group Components
        const columnGroup = document.getElementById("column-toggle-group");
        const rowGroup = document.querySelector('.btn-group-segmented[id="metric-toggle-group"]:has(input[name="row_metric"])') 
                         || document.getElementById("dropdown-toggle-btn-1").closest(".btn-group-segmented");
        const metricGroup = document.querySelector('.btn-group-segmented[id="metric-toggle-group"]:has(input[name="dashboard_metric"])') 
                            || document.getElementById("dropdown-toggle-btn").closest(".btn-group-segmented");
        
        // Custom Date Elements
        const fromDateInput = document.getElementById("from_date");
        const toDateInput = document.getElementById("to_date");

        // 1. Automatically populate initial default tracking dates (Jan 1st, 2026 to Today)
        (function setDefaultDates() {
            if (!fromDateInput || !toDateInput) return;
            const today = new Date();
            const currentYear = today.getFullYear(); // 2026

            const mm = String(today.getMonth() + 1).padStart(2, '0');
            const dd = String(today.getDate()).padStart(2, '0');

            fromDateInput.value = `${currentYear}-01-01`;
            toDateInput.value = `${currentYear}-${mm}-${dd}`;
        })();

        // 2. Toggle Dropdown UI Visibility for Dashboard Metrics ("More" #1)
        if (toggleBtnMetric && menuPanelMetric) {
            $(toggleBtnMetric).off("click").on("click", function (event) {
                event.stopPropagation();
                $(menuPanelRow).removeClass("open"); 
                menuPanelMetric.classList.toggle("open");
            });
        }

        // 3. Toggle Dropdown UI Visibility for Row Metrics ("More" #2)
        if (toggleBtnRow && menuPanelRow) {
            $(toggleBtnRow).off("click").on("click", function (event) {
                event.stopPropagation();
                $(menuPanelMetric).removeClass("open"); 
                menuPanelRow.classList.toggle("open");
            });
        }

        // 4. Extract input states bundle (All 5 values) and trigger data fetch
        function triggerDashboardFetch() {
            const activeColumnEl = columnGroup ? columnGroup.querySelector('input[name="dashboard_period"]:checked') : null;
            const selectedColumnType = activeColumnEl ? activeColumnEl.id : null;

            const fromDateValue = fromDateInput ? fromDateInput.value : null;
            const toDateValue = toDateInput ? toDateInput.value : null;

            const activeRowEl = rowGroup ? rowGroup.querySelector('input[name="row_metric"]:checked') : null;
            const selectedRowMetric = activeRowEl ? activeRowEl.id : null;

            const activeMetricEl = metricGroup ? metricGroup.querySelector('input[name="dashboard_metric"]:checked') : null;
            const selectedDashboardMetric = activeMetricEl ? activeMetricEl.id : null;

            fetchDashboardData(fromDateValue, toDateValue, selectedColumnType, selectedRowMetric, selectedDashboardMetric);
        }

        // 5. Bind change detection listeners across all items
        if (columnGroup) $(columnGroup).off("change").on("change", triggerDashboardFetch);
        if (rowGroup) $(rowGroup).off("change").on("change", triggerDashboardFetch);
        if (metricGroup) $(metricGroup).off("change").on("change", triggerDashboardFetch);
        if (fromDateInput) $(fromDateInput).off("change").on("change", triggerDashboardFetch);
        if (toDateInput) $(toDateInput).off("change").on("change", triggerDashboardFetch);

        // 6. ISOLATED DROPDOWN EVENT HANDLER (FIXED FOR TARGET HIGHLIGHTS)
        $(document).off("click.dropdown-cleanup").on("click.dropdown-cleanup", function (event) {
            
            // Handle row metrics dropdown panel (More 1)
            if (menuPanelRow && menuPanelRow.contains(event.target)) {
                if (event.target.classList.contains("dropdown-item")) {
                    menuPanelRow.classList.remove("open");
                    toggleBtnRow.classList.add("active");
                }
                return;
            }

            // Handle dashboard metrics dropdown panel (More 2)
            if (menuPanelMetric && menuPanelMetric.contains(event.target)) {
                if (event.target.classList.contains("dropdown-item")) {
                    menuPanelMetric.classList.remove("open");
                    toggleBtnMetric.classList.add("active");
                }
                return;
            }

            // Clear button highlights if picking a main visible choice instead
            if (event.target.name === "row_metric") {
                toggleBtnRow.classList.remove("active");
            }
            if (event.target.name === "dashboard_metric") {
                toggleBtnMetric.classList.remove("active");
            }

            // Close all dropdown panels when clicking outside control rows
            if (!event.target.closest(".btn-group-segmented")) {
                if (menuPanelMetric) menuPanelMetric.classList.remove("open");
                if (menuPanelRow) menuPanelRow.classList.remove("open");
            }
        });

        triggerDashboardFetch();
    }

    // =====================================================
    // GRID BACKEND API CONNECTOR
    // =====================================================
    function fetchDashboardData(fromDate, toDate, columnType, rowMetric, dashboardMetric) {
        const tableBody = document.querySelector(".frappe-data-table tbody");
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="10" style="text-align: center; padding: 30px; color: #6c757d;">
                        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                        Loading data...
                    </td>
                </tr>`;
        }

        frappe.call({
            method: "ssd_app.my_custom.page.sales_dashboard.sales_dashboard.dashboard_two",
            args: {
                from_date: fromDate,
                to_date: toDate,
                view_type: columnType,
                row_metric: rowMetric,         
                metric_target: dashboardMetric 
            },
            callback: function(r) {
                if (r.message && !r.message.error) {
                    renderFrappeReportGrid(r.message);
                } else {
                    if (tableBody) {
                        tableBody.innerHTML = `<tr><td colspan="10" style="color: #ff5858; text-align: center; padding: 20px;">Error reading data from source controller.</td></tr>`;
                    }
                }
            }
        });
    }

    // =====================================================
    // NATIVE GRID REPORT DISPLAY RENDERING ENGINE
    // =====================================================
    function renderFrappeReportGrid(records) {
        const tableBody = document.querySelector(".frappe-data-table tbody");
        const tableHead = document.querySelector(".frappe-data-table thead tr");
        if (!tableBody || !tableHead) return;

        tableHead.innerHTML = "";
        tableBody.innerHTML = "";

        if (!records || records.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="10" style="text-align: center; color: #8c99a6; padding: 40px; font-size: 14px;">
                        <i class="fa fa-frown-o" style="font-size: 18px; margin-right: 5px;"></i> No Records Found
                    </td>
                </tr>`;
            return;
        }

        const columns = Object.keys(records[0]);
        const moneyFields = ["sales", "purchase", "cost", "profit", "freight", "local_exp", "commission", "amount", "rate", "pct"];

        // Render Table Headers
        columns.forEach(col => {
            const th = document.createElement("th");
            th.style.padding = "10px 15px";
            th.style.fontSize = "12px";
            th.style.fontWeight = "600";
            th.style.color = "#515b66";
            th.style.backgroundColor = "#f3f5f7";
            th.style.borderBottom = "2px solid #d1d8dc";
            th.style.position = "sticky";
            th.style.top = "0";
            th.style.zIndex = "10";
            
            const isMoney = moneyFields.some(f => col.toLowerCase().includes(f));
            th.style.textAlign = isMoney ? "right" : "left";

            th.textContent = col.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
            tableHead.appendChild(th);
        });

        // Render Data Rows
        records.forEach((row, rowIndex) => {
            const tr = document.createElement("tr");
            tr.style.backgroundColor = rowIndex % 2 === 0 ? "#ffffff" : "#fcfcfc";
            tr.className = "report-data-row";

            columns.forEach(col => {
                const td = document.createElement("td");
                let rawValue = row[col];

                td.style.padding = "10px 15px";
                td.style.fontSize = "13px";
                td.style.color = "#242a30";
                td.style.borderBottom = "1px solid #e2e7ec";
                td.style.whiteSpace = "nowrap";

                const isMoneyCol = moneyFields.some(f => col.toLowerCase().includes(f));

                // 1. Handle Empty states
                if (rawValue === null || rawValue === undefined || rawValue === "") {
                    td.textContent = "—";
                    td.style.color = "#b0b8c0";
                    td.style.textAlign = "left";
                } 
                // 2. FAST STRIP TRICK: If it's a money column, extract just the text value from the HTML instantly
                else if (isMoneyCol) {
                    let cleanText = String(rawValue);
                    if (cleanText.includes("<")) {
                        const tempDiv = document.createElement("div");
                        tempDiv.innerHTML = cleanText;
                        cleanText = tempDiv.textContent || tempDiv.innerText || "";
                    }
                    
                    td.textContent = cleanText.trim();
                    td.style.textAlign = "right";
                    td.style.fontFamily = "monospace";
                }
                // 3. Date field fallback formats
                else if (col.toLowerCase().includes("date") && typeof rawValue === "string") {
                    td.textContent = frappe.datetime.str_to_user(rawValue) || rawValue;
                    td.style.textAlign = "left";
                }
                // 4. Default structural string display fallback
                else {
                    td.textContent = String(rawValue);
                    td.style.textAlign = "left";
                }

                tr.appendChild(td);
            });
            tableBody.appendChild(tr);
        });
    }

// -*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*-


    load_month_summary();
    initDashboardFilters();
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


