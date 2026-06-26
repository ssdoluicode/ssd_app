import frappe
from datetime import datetime, date, timedelta
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}

    from_date = filters.get('from_date')
    to_date = filters.get('to_date')
    group_by = filters.get('group_by') or "Customer"
    column_by = filters.get('column') or "Monthly"
    value_by = filters.get('value') or "sales"

    try:
        # =====================================================
        # 1. MAP THE ROW GROUP METRIC
        # =====================================================
        row_map = {
            "Customer": "IFNULL(cus.customer, '## Unknown Customer')",
            "Category": "IFNULL(pcat.product_category, '## Unknown Category')",
            "Notify": "IFNULL(noti.notify, '## Unknown Notify')",
            "Company": "IFNULL(com.company_code, '## Unknown Company')",
            "Supplier": "IFNULL(cost.supplier, '## Unknown Supplier')",
            "To Country": "IFNULL(cif.to_country, '## Unknown Destination')",
            "From Country": "IFNULL(cif.from_country, '## Unknown Source')"
        }
        row_field = row_map.get(group_by, "IFNULL(cus.customer, '## Unknown Customer')")
        row_alias = group_by.upper().replace(" ", "_")

        # =====================================================
        # 2. MAP THE VALUE METRIC EXPRESSION
        # =====================================================
        metric_map = {
            "sales": "IFNULL(cif.sales, 0)",
            "purchase": "IFNULL(cost.purchase, 0)",
            "cost": "IFNULL(cost.cost, 0)",
            "freight": "IFNULL(exp.freight, 0)",
            "local_exp": "IFNULL(exp.local_exp, 0)",
            "comm": "IFNULL(cost.commission, 0)",
            "profit": "(IFNULL(cif.sales, 0) - IFNULL(cost.cost, 0))",
            "profit_pct": "0"  
        }
        val_expr = metric_map.get(value_by, "IFNULL(cif.sales, 0)")

        # =====================================================
        # 3. DYNAMICALLY GENERATE PIVOT TIME COLUMNS
        # =====================================================
        start_dt = datetime.strptime(from_date, "%Y-%m-%d") if from_date else datetime(2026, 1, 1)
        end_dt = datetime.strptime(to_date, "%Y-%m-%d") if to_date else datetime(2026, 12, 31)
        
        pivot_columns = []
        loop_dt = start_dt

        if column_by == "Quarterly":
            visited_quarters = set()
            while loop_dt <= end_dt:
                yr = loop_dt.year
                qtr = (loop_dt.month - 1) // 3 + 1
                q_key = f"Q{qtr}-{yr}"
                if q_key not in visited_quarters:
                    pivot_columns.append({
                        "label": q_key,
                        "sql_cond": f"cif.inv_date BETWEEN '{yr}-{(qtr-1)*3+1:02d}-01' AND LAST_DAY('{yr}-{qtr*3:02d}-01')"
                    })
                    visited_quarters.add(q_key)
                loop_dt += timedelta(days=20)
                
        elif column_by == "Yearly":
            while loop_dt.year <= end_dt.year:
                yr = loop_dt.year
                pivot_columns.append({
                    "label": f"Year-{yr}",
                    "sql_cond": f"cif.inv_date BETWEEN '{yr}-01-01' AND '{yr}-12-31'"
                })
                if loop_dt.year == end_dt.year: break
                loop_dt = datetime(yr + 1, 1, 1)
     
        else:  # "Monthly"
            while loop_dt <= end_dt:
                m_label = loop_dt.strftime("%b-%Y")
                yr = loop_dt.year
                mn = loop_dt.month
                pivot_columns.append({
                    "label": m_label,
                    "sql_cond": f"cif.inv_date BETWEEN '{yr}-{mn:02d}-01' AND LAST_DAY('{yr}-{mn:02d}-01')"
                })
                next_month = loop_dt.month + 1 if loop_dt.month < 12 else 1
                next_year = loop_dt.year if loop_dt.month < 12 else loop_dt.year + 1
                loop_dt = datetime(next_year, next_month, 1)

        # =====================================================
        # 4. BUILD THE CONDITIONAL AGGREGATIONS
        # =====================================================
        pivot_select_chunks = []
        for col in pivot_columns:
            col_field_alias = col['label'].replace("-", "_")
            chunk = f"""
                SUM(CASE WHEN {col['sql_cond']} THEN IFNULL(cif.sales, 0) ELSE 0 END) AS `raw_sales_{col_field_alias}`,
                SUM(CASE WHEN {col['sql_cond']} THEN IFNULL(cost.cost, 0) ELSE 0 END) AS `raw_cost_{col_field_alias}`
            """
            if value_by != "profit_pct":
                chunk += f", SUM(CASE WHEN {col['sql_cond']} THEN {val_expr} ELSE 0 END) AS `{col_field_alias}`"
            
            pivot_select_chunks.append(chunk.strip())
            
        pivot_sql_string = ",\n                ".join(pivot_select_chunks)

        grand_total_string = """
            SUM(IFNULL(cif.sales, 0)) AS `raw_total_sales`,
            SUM(IFNULL(cost.cost, 0)) AS `raw_total_cost`
        """
        if value_by != "profit_pct":
            grand_total_string += f", SUM({val_expr}) AS `GRAND_TOTAL`"

        # =====================================================
        # 5. ASSEMBLE & EXECUTE SQL TEMPLATE
        # =====================================================
        query = f"""
            SELECT 
                {row_field} AS `{row_alias}`,
                {pivot_sql_string},
                {grand_total_string}
            FROM `tabCIF Sheet` cif
            LEFT JOIN `tabShipping Book` sb ON sb.name = cif.inv_no
            LEFT JOIN `tabCompany` com ON cif.accounting_company = com.name
            LEFT JOIN `tabProduct Category` pcat ON cif.category = pcat.name
            LEFT JOIN `tabCustomer` cus ON sb.customer = cus.name
            LEFT JOIN `tabNotify` noti ON sb.notify = noti.name
            LEFT JOIN `tabPort` lport ON cif.load_port = lport.name
            LEFT JOIN `tabPort` dport ON cif.destination_port = dport.name
            LEFT JOIN (
                SELECT 
                    cost_s.name, 
                    cost_s.inv_no, 
                    cost_s.purchase,
                    cost_s.commission, 
                    cost_s.cost, 
                    IFNULL(sup.supplier, '## Misc Supplier') AS supplier
                FROM `tabCost Sheet` cost_s 
                LEFT JOIN `tabSupplier` sup ON sup.name = cost_s.supplier 
            ) cost ON cif.name = cost.inv_no
            LEFT JOIN (
                SELECT 
                    ec.parent,
                    SUM(CASE WHEN ec.expenses = 'Freight' THEN ec.amount_usd ELSE 0 END) AS freight,
                    SUM(CASE WHEN ec.expenses = 'Local Exp' THEN ec.amount_usd ELSE 0 END) AS local_exp
                FROM `tabExpenses Cost` ec
                GROUP BY 
                    ec.parent
                ORDER BY 
                    ec.parent
            ) exp ON exp.parent= cost.name
            WHERE 
                cost.cost > 0
                AND (%(from_date)s IS NULL OR %(to_date)s IS NULL OR cif.inv_date BETWEEN %(from_date)s AND %(to_date)s)
            GROUP BY 
                {row_field}
            ORDER BY 
                `raw_total_sales` DESC
        """
        query_params = {
            "from_date": from_date if from_date else None,
            "to_date": to_date if to_date else None
        }

        raw_records = frappe.db.sql(query, query_params, as_dict=True)
        records = []

        # =====================================================
        # 6. POST-PROCESS ROWS & COMPUTE METRICS
        # =====================================================
        for row in raw_records:
            new_row = {row_alias: row[row_alias]}
            
            for col in pivot_columns:
                label = col['label']
                col_field_alias = label.replace("-", "_")
                if value_by == "profit_pct":
                    r_sales = row.get(f"raw_sales_{col_field_alias}", 0) or 0
                    r_cost = row.get(f"raw_cost_{col_field_alias}", 0) or 0
                    new_row[col_field_alias] = round(((r_sales - r_cost) / r_cost * 100), 2) if r_cost > 0 else 0.0
                else:
                    new_row[col_field_alias] = float(row.get(col_field_alias, 0) or 0)

            if value_by == "profit_pct":
                tot_sales = row.get("raw_total_sales", 0) or 0
                tot_cost = row.get("raw_total_cost", 0) or 0
                new_row["GRAND_TOTAL"] = round(((tot_sales - tot_cost) / tot_cost * 100), 2) if tot_cost > 0 else 0.0
            else:
                new_row["GRAND_TOTAL"] = float(row.get("GRAND_TOTAL", 0) or 0)

            for k, v in row.items():
                if k.startswith("raw_"):
                    new_row[k] = v
            records.append(new_row)

        # =====================================================
        # 7. COLUMNS STRUCTURE METADATA
        # =====================================================
        is_profit_pct = (value_by == "profit_pct")
        fieldtype = "Float"
        precision = 2 if is_profit_pct else 0
        
        columns = [{"label": _(group_by), "fieldname": row_alias, "fieldtype": "Data", "width": 180}]

        for col in pivot_columns:
            columns.append({
                "label": _(col["label"]),
                "fieldname": col['label'].replace("-", "_"),
                "fieldtype": fieldtype,
                "precision": precision,
                "width": 120
            })

        columns.append({"label": _("Grand Total"), "fieldname": "GRAND_TOTAL", "fieldtype": fieldtype, "precision": precision, "width": 140})

        # =====================================================
        # 8. PREPARE THE TOTAL ROW (NATIVE RAW NUMBERS)
        # =====================================================
        python_total_row = {row_alias: "Total"}

        if is_profit_pct:
            grand_sales_all = sum(r.get("raw_total_sales", 0) or 0 for r in records)
            grand_cost_all = sum(r.get("raw_total_cost", 0) or 0 for r in records)
            python_total_row["GRAND_TOTAL"] = round(((grand_sales_all - grand_cost_all) / grand_cost_all * 100), 2) if grand_cost_all > 0 else 0.0
        else:
            python_total_row["GRAND_TOTAL"] = float(sum(r.get("GRAND_TOTAL", 0) or 0 for r in records))

        for col in pivot_columns:
            col_field_alias = col['label'].replace("-", "_")
            if is_profit_pct:
                periodic_sales_sum = sum(r.get(f"raw_sales_{col_field_alias}", 0) or 0 for r in records)
                periodic_cost_sum = sum(r.get(f"raw_cost_{col_field_alias}", 0) or 0 for r in records)
                python_total_row[col_field_alias] = round(((periodic_sales_sum - periodic_cost_sum) / periodic_cost_sum * 100), 2) if periodic_cost_sum > 0 else 0.0
            else:
                python_total_row[col_field_alias] = float(sum(r.get(col_field_alias, 0) or 0 for r in records))

        if records:
            records.append(python_total_row)

        # =====================================================
        # 9. GENERATE CHART (Fixed Missing Parenthesis syntax error here)
        # =====================================================
        labels = []
        time_totals = []
        for col in pivot_columns:
            col_field_alias = col['label'].replace("-", "_")
            labels.append(col['label'])
            if is_profit_pct:
                period_sales = sum(r.get(f"raw_sales_{col_field_alias}", 0) or 0 for r in records[:-1])
                period_cost = sum(r.get(f"raw_cost_{col_field_alias}", 0) or 0 for r in records[:-1])
                time_totals.append(round(((period_sales - period_cost) / period_cost * 100), 2) if period_cost > 0 else 0.0)
            else:
                time_totals.append(sum(r.get(col_field_alias, 0) or 0 for r in records[:-1]))

        chart = {
            "data": {
                "labels": labels,
                "datasets": [{"name": _(value_by.replace("_", " ").title()), "values": time_totals}]
            },
            "type": "bar",
            "colors": ["#765eff"]
        }

        return columns, records, None, chart

    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="Execute Matrix Report Error")
        return [], [], None, None

@frappe.whitelist()
def show_inv_wise(group_by, head, period):
    filter_data_dict = {
        "Customer": {"dc": "tabCustomer", "jdc":"sb", "as":"cus", "field": "code", "l_field": "customer"},
        "Notify": {"dc": "tabNotify","jdc":"sb", "as":"noti", "field": "code", "l_field": "notify"},
        "Category": {"dc": "tabProduct Category", "jdc":"cif", "as":"pc", "field": "product_category", "l_field": "category"},
        "From Country": {"dc": "tabCountry", "jdc":"cif", "as":"fc", "field": "country_name", "l_field": "from_country"},
        "To Country": {"dc": "tabCountry", "jdc":"cif", "as":"tc", "field": "country_name", "l_field": "to_country"},
        "Company": {"dc": "tabCompany", "jdc":"cif", "as":"com", "field": "company_code", "l_field": "accounting_company"}
    }
    month_map= {"jan":1, "feb":2, "mar":3, "apr":4, "may":5, "jun":6, "jul":7, "aug":8, "sep":9, "oct":10, "nov":11, "dec":12}
    period_clean = period.strip().replace("-", "_")

    if period_clean.lower() == "total" or period_clean.lower() == "grand_total":
        period_filter = "1=1"
        
    elif (len(period_clean)==7):
        # Handles Quarterly formats like "Q2_2026" or "Q2-2026"
        quarter_str, year = period_clean.lower().split("_")
        period_filter = f"YEAR(cif.inv_date) = '{year}' AND QUARTER(cif.inv_date) = '{quarter_str[-1]}'"
        
    elif (len(period_clean)==8):
        # Handles Monthly formats like "Jan_2026" or "Jan-2026"
        month, year = period_clean.split("_")
        
        # Guard against 2026_01 raw numeric format cases if they happen
        if month.lower() in month_map:
            month_number = month_map[month.lower()]
        else:
            month_number = int(month)
            
        period_filter = f"MONTH(cif.inv_date) = '{month_number}' AND YEAR(cif.inv_date) = '{year}'"
        
    else:
        # Fallback for Yearly format like "Year-2026"
        month, year = period_clean.split("_")
        period_filter = f"YEAR(cif.inv_date) = '{year}'"

    filter_field = filter_data_dict[group_by]["field"]
    as_name = filter_data_dict[group_by]["as"]
    filters={
        "head": head
    }
    data = frappe.db.sql(f"""
        SELECT 
            cif.name, 
            cif.invoice_no AS inv_no, 
            cif.inv_date, 
            pc.product_category AS Category, 
            cus.code AS Customer, 
            noti.code AS Notify, 
            cif.sales, 
            cif.document, 
            cif.cc 
        FROM `tabCIF Sheet` cif 
        LEFT JOIN `tabProduct Category` pc ON pc.name = cif.category
        LEFT JOIN `tabShipping Book` sb ON sb.name=cif.inv_no
        LEFT JOIN `tabCustomer` cus ON cus.name = sb.customer
        LEFT JOIN `tabNotify` noti ON noti.name = sb.notify
        LEFT JOIN `tabCountry` fc ON fc.name = cif.from_country
        LEFT JOIN `tabCountry` tc ON tc.name = cif.to_country
        LEFT JOIN `tabCompany` com ON com.name = cif.accounting_company
        WHERE {period_filter}
        AND {as_name}.{filter_field} = %(head)s
        
        ORDER BY cif.inv_date DESC
    """, filters, as_dict=True)


    if not data:
        return "<p>No data found.</p>"
    
    total_sales = sum(row.sales or 0 for row in data)
    total_document = sum(row.document or 0 for row in data)
    total_cc = sum(row.cc or 0 for row in data)

    # Build HTML table
    html = """
    <style>
        .cif-table-container {
            max-height: 75vh;
            overflow: auto;
        }
        table.cif-table {
            border-collapse: collapse;
            width: 100%;
            font-size: 13px;
            min-width: 1000px;
        }
        table.cif-table th, table.cif-table td {
            border: 1px solid #ddd;
            padding: 6px;
            text-align: left;
            white-space: nowrap;
        }
        table.cif-table th {
            background-color: #f5f5f5;
            position: sticky;
            top: 0;
            z-index: 1;
        }
        
    </style>
    <table class="cif-table">
        <thead>
            <tr>
                <th style="text-align:center;">Inv No</th>
                <th style="text-align:center;">Inv Date</th>
                <th style="text-align:center;">Category</th>
                <th style="text-align:center;">Customer</th>
                <th style="text-align:center;">Notify</th>
                <th style="text-align:center;">Sales</th>
                <th style="text-align:center;">Document</th>
                <th style="text-align:center;">CC</th>
            </tr>
        </thead>
        <tbody>
    """

    for row in data:
        html += f"""
            <tr>

                <td><a style="color:blue;" href="#" onclick="showCIFDetails('{row.name}', '{row.inv_no}');">{row.inv_no}</a></td>
                <td>{row.inv_date }</td>
                <td>{row.Category or ""}</td>
                <td>{row.Customer or ""}</td>
                <td>{row.Notify or ""}</td>
                <td style="text-align:right;">{'{:,.2f}'.format(row.sales or 0)}</td>
                <td style="text-align:right;">{'{:,.2f}'.format(row.document or 0)}</td>
                <td style="text-align:right;">{'{:,.2f}'.format(row.cc or 0)}</td>
            </tr>
        """

    # Add tfoot with totals
    html += f"""
        </tbody>
        <tfoot>
            <tr>
                <td colspan="5" style="text-align:center;">Total</td>
                <td style="text-align:right;">{'{:,.2f}'.format(total_sales)}</td>
                <td style="text-align:right;">{'{:,.2f}'.format(total_document)}</td>
                <td style="text-align:right;">{'{:,.2f}'.format(total_cc)}</td>
            </tr>
        </tfoot>
    </table>"""

    return html



@frappe.whitelist()
def get_first_jan_of_max_year():
    # Find highest year of inv_date
    max_year = frappe.db.sql("""
        SELECT MAX(YEAR(inv_date))
        FROM `tabCIF Sheet`
        WHERE inv_date IS NOT NULL
    """)[0][0]

    if not max_year:
        return None

    # Always return 1st Jan of that year
    return f"{max_year}-01-01"