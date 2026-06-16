frappe.pages['sales-dashboard'].on_page_load = function (wrapper) {

    const page = frappe.ui.make_app_page({
        parent: wrapper,
        // title: "Enterprise Performance View",
        single_column: true
    });

    page.main.html(frappe.render_template("sales_dashboard"));

    // Scoped Central Application Memory Cache & State Engine Map
    let appState = {
        charts: {},
        current_db1_data: [],
        raw_matrix_dataset: [], // Stores total raw data cache from the backend endpoint
        sort_key: 'GRAND TOTAL',
        sort_order: 'desc',
        debounce_timer: null,
        moneyFields: ["sales", "purchase", "cost", "profit", "freight", "local_exp", "commission", "amount", "rate", "total", "grand total"]
    };

    // Parallel Dashboards Modules Init Execution Pass
    init_dashboard_one();
    init_dashboard_two();

    // =========================================================================
    // CORE MODULE: DASHBOARD 1 (SIDEBAR TREND GRAPH CANVASES LAYER)
    // =========================================================================
    function init_dashboard_one() {
        frappe.call({
            method: "ssd_app.my_custom.page.sales_dashboard.sales_dashboard.get_month_summary",
            freeze: true,
            callback: r => {
                let data = r.message || [];
                render_monthly_cubes(data);
                if (data.length) {
                    load_db1_details(data[0].month, data[0].period_type);
                }
            }
        });
    }

    function load_db1_details(month, period_type) {
        let isMonth = (period_type === "month");
        let args = isMonth ? { year: month.split("-")[0], month: month.split("-")[1] } : { year: month.split("-")[1] };
        let default_group = isMonth ? "Category" : "Month";

        frappe.call({
            method: "ssd_app.my_custom.page.sales_dashboard.sales_dashboard.get_data",
            args,
            freeze: true,
            callback: r => {
                appState.current_db1_data = r.message || [];
                render_db1_interface(appState.current_db1_data, default_group);
            }
        });
    }

    function render_monthly_cubes(data) {
        let html = data.map((r, i) => {
            let sales = flt(r.sales);
            let sales_nc = flt(r.sales_nc);
            let profit = sales - flt(r.cost);
            let pct = sales ? ((profit / flt(r.cost)) * 100).toFixed(2) : 0;

            let sales_nc_html = sales_nc ? `
                <div class="cube-row">
                    <div class="cube-label">Sales (Cost Pending)</div>
                    <div class="cube-value">${format_number(sales_nc)}</div>
                </div>` : "";

            return `
                <div class="cube-card ${i === 0 ? 'active-cube' : ''}" data-month="${r.month}" data-period_type="${r.period_type}">
                    <div class="cube-month">${r.month}</div>
                    <div class="cube-row">
                        <div class="cube-label">Sales Vol</div>
                        <div class="cube-value">${format_number(sales)}</div>
                    </div>
                    ${sales_nc_html}
                    <div class="cube-row">
                        <div class="cube-label">Gross Margin</div>
                        <div class="cube-value ${profit >= 0 ? 'margin-good':'margin-bad'}">
                            ${format_number(profit)} <span class="profit-pct">(${pct}%)</span>
                        </div>
                    </div>
                </div>`;
        }).join("");

        $(".monthly-cubes").html(html).off("click", ".cube-card").on("click", ".cube-card", function () {
            $(".cube-card").removeClass("active-cube");
            $(this).addClass("active-cube");
            load_db1_details($(this).data("month"), $(this).data("period_type"));
        });
    }

    function render_db1_interface(data, default_group) {
        const CONFIG = [
            { id: "customer", title: "Customer Wise" },
            { id: "notify", title: "Notify Wise" },
            { id: "company", title: "Company Wise" },
            { id: "country", title: "Country Wise" }
        ];

        let cardsHtml = CONFIG.map(c => `
            <div class="pie-card">
                <h5 class="pie-title">${c.title}</h5>
                <div id="pie-${c.id}"></div>
            </div>
        `).join("");

        $(".analysis-content").html(`
            <div class="analysis-filters mb-3">
                <select id="group-by-select" class="form-control" style="width:200px;">
                    <option>Category</option><option>Customer</option>
                    <option>Notify</option><option>Month</option>
                </select>
                <select id="based_on" class="form-control" style="width:200px;">
                    <option>Sales</option><option>Gross Profit</option><option>Finance Cost</option>
                </select>
            </div>
            <div class="pie-inline-wrapper">${cardsHtml}</div>
            <div class="chart-row mt-4">
                <div class="bar-card"><h5>Gross Revenue Metric</h5><div id="chart-sales"></div></div>
                <div class="bar-card"><h5>Gross Profit Spread</h5><div id="chart-g-profit"></div></div>
                <div class="bar-card"><h5>Finance Cost Overhead</h5><div id="chart-f-cost"></div></div>
            </div>
        `);

        $("#group-by-select").val(default_group);
        
        const triggerSummaryTables = () => {
            let based_on = $("#based_on").val();
            CONFIG.forEach(c => render_summary_table(`pie-${c.id}`, data, c.id, based_on));
        };

        $(".analysis-content").off("change", "#based_on").on("change", "#based_on", triggerSummaryTables);
        $(".analysis-content").off("change", "#group-by-select").on("change", "#group-by-select", update_db1_charts);

        triggerSummaryTables();
        update_db1_charts();
    }

    function update_db1_charts() {
        let fieldMap = { Category: "category", Customer: "customer", Notify: "notify", Month: "month" };
        let currentField = fieldMap[$("#group-by-select").val()] || "category";
        ["sales", "g-profit", "f-cost"].forEach(m => render_db1_bar_chart(appState.current_db1_data, currentField, m));
    }

    function render_db1_bar_chart(data, field, metric) {
        let grouped = {};
        data.forEach(r => {
            let key = r[field] || "Unknown Node Space";
            if (!grouped[key]) grouped[key] = { sales: 0, g_profit: 0, f_cost: 0 };
            grouped[key].sales += flt(r.total_sales);
            grouped[key].g_profit += flt(r.total_g_profit);
            grouped[key].f_cost += flt(r.total_f_cost);
        });

        let rows = Object.keys(grouped).map(k => {
            let val = 0;
            if (metric === "sales") val = grouped[k].sales;
            if (metric === "g-profit") val = grouped[k].g_profit;
            if (metric === "f-cost") val = grouped[k].f_cost;
            return { label: k, value: Math.round(val) };
        });

        rows.sort((a, b) => (!isNaN(Number(a.label)) && !isNaN(Number(b.label))) ? Number(a.label) - Number(b.label) : String(a.label).localeCompare(String(b.label)));

        let chartId = `#chart-${metric}`;
        if (appState.charts[metric]) appState.charts[metric].destroy();

        let colorsMap = { "sales": "#2563eb", "g-profit": "#16a34a", "f-cost": "#f97316" };

        appState.charts[metric] = new frappe.Chart(chartId, {
            data: { labels: rows.map(r => r.label), datasets: [{ name: metric.toUpperCase(), values: rows.map(r => r.value) }] },
            type: "bar",
            colors: [colorsMap[metric] || "#2563eb"],
            axisOptions: { shortenYAxisNumbers: true, yAxis: { numberFormatter: v => format_km(v) } },
            tooltipOptions: { formatTooltipY: v => v ? format_km(v) : "" }
        });
    }

    function render_summary_table(id, data, field, based_on) {
        let valueField = { "Sales": "total_sales", "Gross Profit": "total_g_profit", "Finance Cost": "total_f_cost" }[based_on] || "total_sales";
        let map = {}, total = 0;

        data.forEach(r => {
            let k = r[field] || "Unknown";
            let v = flt(r[valueField]);
            total += v;
            map[k] = (map[k] || 0) + v;
        });

        let rowsHtml = Object.keys(map)
            .sort((a, b) => map[b] - map[a])
            .slice(0, 10)
            .map(k => {
                let amt = Math.round(map[k]);
                let pct = total ? ((amt / total) * 100).toFixed(2) : 0;
                return `
                    <div class="mini-row">
                        <div class="mini-name">${k}</div>
                        <div class="mini-right">
                            <div class="mini-amount">${amt.toLocaleString("en-US")}</div>
                            <div class="mini-badge">${pct}%</div>
                        </div>
                    </div>`;
            }).join("");

        $("#" + id).html(`<div class="mini-table">${rowsHtml}</div>`);
    }

    // =========================================================================
    // REFACTORED CORE MODULE: DASHBOARD 2 (HIGH-SPEED ON-THE-FLY PIVOT MATRIX ENGINE)
    // =========================================================================
    function init_dashboard_two() {
        const fromDateInput = document.getElementById("from_date");
        const toDateInput = document.getElementById("to_date");

        if (fromDateInput && toDateInput) {
            const today = new Date();
            const mm = String(today.getMonth() + 1).padStart(2, '0');
            const dd = String(today.getDate()).padStart(2, '0');
            fromDateInput.value = `${today.getFullYear()}-01-01`;
            toDateInput.value = `${today.getFullYear()}-${mm}-${dd}`;
        }

        const triggerBackendFetch = () => {
            let fromDate = $("#from_date").val();
            let toDate = $("#to_date").val();
            fetch_db2_raw_data(fromDate, toDate);
        };

        const rebuildMatrixUIInstantly = () => {
            process_and_render_matrix_data();
        };

        $(".dashboard-controls-row").on("change", "input[type='radio']", rebuildMatrixUIInstantly);

        $(".dashboard-controls-row").on("input change", "input[type='date']", function(e) {
            clearTimeout(appState.debounce_timer);
            if (e.type === 'change' && (!e.originalEvent || e.originalEvent.inputType === undefined)) {
                triggerBackendFetch();
                return;
            }
            appState.debounce_timer = setTimeout(() => {
                triggerBackendFetch();
            }, 500);
        });

        const bindDropdown = (btnId, panelId, counterpartPanelId) => {
            $(`#${btnId}`).off("click").on("click", function(e) {
                e.stopPropagation();
                $(`#${counterpartPanelId}`).removeClass("open");
                $(`#${panelId}`).toggleClass("open");
            });

            $(`#${panelId}`).off("click", ".dropdown-item").on("click", ".dropdown-item", function() {
                $(`#${panelId}`).removeClass("open");
                $(`#${btnId}`).addClass("active");
            });
        };

        bindDropdown("row-dropdown-btn", "row-dropdown-panel", "metric-dropdown-panel");
        bindDropdown("metric-dropdown-btn", "metric-dropdown-panel", "row-dropdown-panel");

        $('input[name="row_metric"]').on("change", function() { if(!$(this).closest('.dropdown-menu-panel').length) $("#row-dropdown-btn").removeClass("active"); });
        $('input[name="dashboard_metric"]').on("change", function() { if(!$(this).closest('.dropdown-menu-panel').length) $("#metric-dropdown-btn").removeClass("active"); });

        $(document).on("click", function(e) {
            if (!$(e.target).closest(".btn-group-segmented").length) {
                $(".dropdown-menu-panel").removeClass("open");
            }
        });

        triggerBackendFetch();
    }

    function show_matrix_status_notice(message, type="info") {
        const tableBody = document.querySelector(".frappe-data-table tbody");
        if (!tableBody) return;
        let styleClass = type === "warning" ? "text-warning font-weight-bold" : "text-muted";
        let iconMarkup = type === "warning" ? "fa-exclamation-triangle" : "fa-keyboard-o";
        tableBody.innerHTML = `<tr><td class="text-center p-4 ${styleClass}"><i class="fa ${iconMarkup}"></i> ${message}</td></tr>`;
    }

    function fetch_db2_raw_data(fromDate, toDate) {
        if (!fromDate || !toDate || fromDate.length < 10 || toDate.length < 10) {
            show_matrix_status_notice("Waiting for a complete date parameters range format...");
            return;
        }

        let fromYear = parseInt(fromDate.split("-")[0], 10);
        let toYear = parseInt(toDate.split("-")[0], 10);
        if (isNaN(fromYear) || isNaN(toYear) || fromYear < 2000 || toYear < 2000) {
            show_matrix_status_notice("Constraint Breach Warning: Selected date fields framework ranges must be >= 2000.", "warning");
            return;
        }

        show_matrix_status_notice("<span class='spinner-border spinner-border-sm' role='status' aria-hidden='true'></span> Extracting core data matrix frames from server database...");

        frappe.call({
            method: "ssd_app.my_custom.page.sales_dashboard.sales_dashboard.dashboard_two",
            args: { from_date: fromDate, to_date: toDate },
            callback: function(r) {
                if (r.message && !r.message.error) {
                    appState.raw_matrix_dataset = r.message;
                    appState.sort_key = 'GRAND TOTAL';
                    appState.sort_order = 'desc';
                    process_and_render_matrix_data();
                } else {
                    show_matrix_status_notice("Data pipeline connection runtime error. Check keys map mapping.", "warning");
                }
            }
        });
    }

    function process_and_render_matrix_data() {
        if (!appState.raw_matrix_dataset || appState.raw_matrix_dataset.length === 0) {
            render_matrix_dom_elements([], [], {});
            return;
        }

        let colType = $('input[name="dashboard_period"]:checked').attr('id'); 
        let rowMetric = $('input[name="row_metric"]:checked').attr('id');     
        let valMetric = $('input[name="dashboard_metric"]:checked').attr('id'); 

        let uniqueRows = new Set();
        let uniqueTimelineColumns = new Set();

        appState.raw_matrix_dataset.forEach(row => {
            let rowKey = row[rowMetric] || "## Unknown Item Workspace";
            uniqueRows.add(rowKey);

            if (row.inv_date) {
                let parts = row.inv_date.split("-");
                if (colType === "per_year") {
                    uniqueTimelineColumns.add(parts[0]);
                } else if (colType === "per_quarter") {
                    let quarter = Math.floor((parseInt(parts[1], 10) - 1) / 3) + 1;
                    uniqueTimelineColumns.add(`${parts[0]}-Q${quarter}`);
                } else { 
                    uniqueTimelineColumns.add(`${parts[0]}-${parts[1]}`);
                }
            }
        });

        let sortedTimelineCols = Array.from(uniqueTimelineColumns).sort();

        // Initialize Dynamic multi-dimensional tracking indices
        let pivotGrid = {};
        // Column Summary accumulators map objects tracking base relational structures
        let columnSummaries = { _totals: { sales: 0, cost: 0, purchase: 0, freight: 0, local: 0, comm: 0 } };

        sortedTimelineCols.forEach(cName => {
            columnSummaries[cName] = { sales: 0, cost: 0, purchase: 0, freight: 0, local: 0, comm: 0 };
        });

        Array.from(uniqueRows).forEach(rName => {
            pivotGrid[rName] = { _totals: { sales: 0, cost: 0, purchase: 0, freight: 0, local: 0, comm: 0 } };
            sortedTimelineCols.forEach(cName => {
                pivotGrid[rName][cName] = { sales: 0, cost: 0, purchase: 0, freight: 0, local: 0, comm: 0 };
            });
        });

        // Loop accumulation values directly into localized structural components
        appState.raw_matrix_dataset.forEach(row => {
            let rowKey = row[rowMetric] || "## Unknown Item Workspace";
            let parts = row.inv_date.split("-");
            let colKey = "";

            if (colType === "per_year") colKey = parts[0];
            else if (colType === "per_quarter") colKey = `${parts[0]}-Q${Math.floor((parseInt(parts[1], 10) - 1) / 3) + 1}`;
            else colKey = `${parts[0]}-${parts[1]}`;

            let bucket = pivotGrid[rowKey][colKey];
            let totBucket = pivotGrid[rowKey]._totals;

            let colSummaryBucket = columnSummaries[colKey];
            let totalSummaryBucket = columnSummaries._totals;

            if (bucket) {
                let s = flt(row.met_sales), c = flt(row.met_cost), p = flt(row.met_purchase);
                let f = flt(row.met_freight), l = flt(row.met_local), cm = flt(row.met_comm);

                // Row accumulation mapping logic
                bucket.sales += s; bucket.cost += c; bucket.purchase += p; bucket.freight += f; bucket.local += l; bucket.comm += cm;
                totBucket.sales += s; totBucket.cost += c; totBucket.purchase += p; totBucket.freight += f; totBucket.local += l; totBucket.comm += cm;

                // Dynamic Column total metrics layout compilation tracking pass
                colSummaryBucket.sales += s; colSummaryBucket.cost += c; colSummaryBucket.purchase += p; colSummaryBucket.freight += f; colSummaryBucket.local += l; colSummaryBucket.comm += cm;
                totalSummaryBucket.sales += s; totalSummaryBucket.cost += c; totalSummaryBucket.purchase += p; totalSummaryBucket.freight += f; totalSummaryBucket.local += l; totalSummaryBucket.comm += cm;
            }
        });

        // COMPUTE VALUES DYNAMICALLY (Ensures correct percentages on total aggregated metrics)
        const computeCellMetric = (dataObj) => {
            if (valMetric === "met_sales") return dataObj.sales;
            if (valMetric === "met_purchase") return dataObj.purchase;
            if (valMetric === "met_cost") return dataObj.cost;
            if (valMetric === "met_freight") return dataObj.freight;
            if (valMetric === "met_local") return dataObj.local;
            if (valMetric === "met_comm") return dataObj.comm;
            if (valMetric === "met_profit") return (dataObj.sales - dataObj.cost);
            if (valMetric === "met_profit_pct") {
                // Correct Margin Formulas: (Sales - Cost) / Cost * 100
                return dataObj.cost ? (((dataObj.sales - dataObj.cost) / dataObj.cost) * 100) : 0;
            }
            return 0;
        };

        // Construct standard localized rows layout payload items
        let rowFieldTitle = rowMetric.replace("row_", "").toUpperCase();
        let matrixRows = Object.keys(pivotGrid).map(rName => {
            let rowRecord = {};
            rowRecord[rowFieldTitle] = rName;

            sortedTimelineCols.forEach(cName => {
                rowRecord[cName] = computeCellMetric(pivotGrid[rName][cName]);
            });

            rowRecord['GRAND TOTAL'] = computeCellMetric(pivotGrid[rName]._totals);
            return rowRecord;
        });

        // Compile complete, independent total summaries tracking row structure map objects
        let bottomSummaryRow = {};
        bottomSummaryRow[rowFieldTitle] = "TOTAL / SUMMARY";
        sortedTimelineCols.forEach(cName => {
            bottomSummaryRow[cName] = computeCellMetric(columnSummaries[cName]);
        });
        bottomSummaryRow['GRAND TOTAL'] = computeCellMetric(columnSummaries._totals);

        render_matrix_dom_elements(matrixRows, [rowFieldTitle, ...sortedTimelineCols, 'GRAND TOTAL'], bottomSummaryRow);
    }

    function render_matrix_dom_elements(records, columns, bottomSummaryRow) {
        const tableHead = document.querySelector(".frappe-data-table thead tr");
        const tableBody = document.querySelector(".frappe-data-table tbody");
        if (!tableBody || !tableHead) return;

        if (records.length === 0) {
            tableHead.innerHTML = "<th>Empty Workspace Scope</th>";
            tableBody.innerHTML = `<tr><td class="text-center text-muted p-4"><i class="fa fa-frown-o"></i> No corresponding metrics match selection scope.</td></tr>`;
            return;
        }

        // Apply Localized Client-Side Fast Sorting (Excludes summary row from target calculations lists)
        if (appState.sort_key && columns.includes(appState.sort_key)) {
            let key = appState.sort_key;
            let multiplier = appState.sort_order === 'asc' ? 1 : -1;
            let isFirstCol = (key === columns[0]);

            records.sort((a, b) => {
                if (isFirstCol) {
                    return String(a[key]).localeCompare(String(b[key])) * multiplier;
                } else {
                    return (flt(a[key]) - flt(b[key])) * multiplier;
                }
            });
        }

        // Render Column Headers
        tableHead.innerHTML = columns.map(col => {
            let isFirst = (col === columns[0]);
            let alignStyle = isFirst ? "text-align: left;" : "text-align: right;";
            let iconClass = "fa fa-sort text-muted-sort";
            
            if (appState.sort_key === col) {
                iconClass = appState.sort_order === 'asc' ? "fa fa-sort-up text-active-sort" : "fa fa-sort-down text-active-sort";
            }
            
            return `
                <th class="report-sort-header" data-col="${col}" style="${alignStyle} cursor: pointer; user-select: none;">
                    <span>${col.replace(/_/g, ' ').toUpperCase()}</span> <i class="${iconClass}"></i>
                </th>`;
        }).join("");

        let currentMetric = $('input[name="dashboard_metric"]:checked').attr('id');
        let htmlRowsContent = [];

        // 1. Build standard relational rows string maps
        records.forEach(row => {
            let rowCells = columns.map((col, idx) => {
                let cellVal = row[col];
                if (idx === 0) {
                    return `<td class="text-left font-weight-bold">${String(cellVal)}</td>`;
                }
                if (cellVal === null || cellVal === undefined || cellVal === 0) {
                    return `<td class="text-muted text-right">—</td>`;
                }
                if (currentMetric === "met_profit_pct") {
                    return `<td class="text-right font-monospace text-primary">${flt(cellVal).toFixed(2)}%</td>`;
                }
                return `<td class="text-right font-monospace">${Math.round(flt(cellVal)).toLocaleString("en-US")}</td>`;
            }).join("");

            htmlRowsContent.push(`<tr class="report-data-row">${rowCells}</tr>`);
        });

        // 2. Build bottom fixed matrix total row metrics string
        if (bottomSummaryRow && Object.keys(bottomSummaryRow).length > 0) {
            let totalCellsHtml = columns.map((col, idx) => {
                let cellVal = bottomSummaryRow[col];
                if (idx === 0) {
                    return `<td class="text-left font-weight-bold text-uppercase" style="background-color: #f1f5f9; position: sticky; bottom: 0; z-index: 5;">${String(cellVal)}</td>`;
                }
                if (cellVal === null || cellVal === undefined || cellVal === 0) {
                    return `<td class="text-muted text-right font-weight-bold" style="background-color: #f1f5f9; position: sticky; bottom: 0; z-index: 5;">—</td>`;
                }
                if (currentMetric === "met_profit_pct") {
                    return `<td class="text-right font-monospace font-weight-bold text-success" style="background-color: #f1f5f9; position: sticky; bottom: 0; z-index: 5;">${flt(cellVal).toFixed(2)}%</td>`;
                }
                return `<td class="text-right font-monospace font-weight-bold" style="background-color: #f1f5f9; position: sticky; bottom: 0; z-index: 5; color: #1e293b;">${Math.round(flt(cellVal)).toLocaleString("en-US")}</td>`;
            }).join("");

            htmlRowsContent.push(`<tr class="report-summary-total-row" style="border-top: 2px solid #cbd5e1; font-weight: bold;">${totalCellsHtml}</tr>`);
        }

        // Direct Core DOM String Builder Injection Pass
        tableBody.innerHTML = htmlRowsContent.join("");

        // Bind Sort Events Click Listeners
        $(".report-sort-header").off("click").on("click", function() {
            let targetCol = $(this).data("col");
            appState.sort_order = (appState.sort_key === targetCol && appState.sort_order === 'desc') ? 'asc' : 'desc';
            appState.sort_key = targetCol;
            render_matrix_dom_elements(records, columns, bottomSummaryRow); 
        });
    }

    function format_number(n) { return Math.round(Number(n) || 0).toLocaleString("en-US"); }
    function format_km(v) {
        v = Number(v) || 0;
        if (Math.abs(v) >= 1000000) return (v / 1000000).toFixed(1) + "M";
        if (Math.abs(v) >= 1000) return (v / 1000).toFixed(1) + "K";
        return Math.round(v);
    }
};