import frappe
from frappe import _
from datetime import datetime, timedelta

# ==============================
# API 1: Sidebar Summary
# ==============================
@frappe.whitelist()
def get_month_summary():
    return frappe.db.sql("""
        SELECT 
    DATE_FORMAT(cif.inv_date,'%Y-%m') AS month,
    "month" AS period_type,
    DATE_FORMAT(cif.inv_date,'%Y%m') AS sort_key,

    ROUND(SUM(CASE 
            WHEN IFNULL(cs.cost,0) > 0 
            THEN cif.sales 
            ELSE 0 
        END),0) AS sales,

    ROUND(IFNULL(SUM(cs.cost),0),0) AS cost,

    --  NEW COLUMN (Sales where cost = 0)
    ROUND(SUM(CASE 
            WHEN IFNULL(cs.cost,0) = 0 
            THEN cif.sales 
            ELSE 0 
        END),0) AS sales_nc,

    ROUND(
        IFNULL(
            (SUM(cif.sales) - IFNULL(SUM(cs.cost),0))
            / NULLIF(SUM(cs.cost),0) * 100
        ,0)
    ,2) AS profit_pct

FROM `tabCIF Sheet` cif
LEFT JOIN `tabCost Sheet` cs 
    ON cs.inv_no = cif.name

GROUP BY YEAR(cif.inv_date), MONTH(cif.inv_date)

UNION ALL

/* =========================
   YEARLY DATA
========================= */
SELECT 
    CONCAT('Year-', DATE_FORMAT(cif.inv_date,'%Y')) AS month,
    "year" AS period_type,
    CONCAT(DATE_FORMAT(cif.inv_date,'%Y'), '99') AS sort_key,

    ROUND(SUM(CASE 
            WHEN IFNULL(cs.cost,0) > 0 
            THEN cif.sales 
            ELSE 0 
        END),0) AS sales,

    ROUND(IFNULL(SUM(cs.cost),0),0) AS cost,

    --  NEW COLUMN (Sales where cost = 0)
    ROUND(SUM(CASE 
            WHEN IFNULL(cs.cost,0) = 0 
            THEN cif.sales 
            ELSE 0 
        END),0) AS sales_nc,

    ROUND(
        IFNULL(
            (SUM(cif.sales) - IFNULL(SUM(cs.cost),0))
            / NULLIF(SUM(cs.cost),0) * 100
        ,0)
    ,2) AS profit_pct

FROM `tabCIF Sheet` cif
LEFT JOIN `tabCost Sheet` cs 
    ON cs.inv_no = cif.name

GROUP BY YEAR(cif.inv_date)

ORDER BY sort_key DESC;
    """, as_dict=True)


# ==============================
# API 2: Selected Month Details
# ==============================

@frappe.whitelist()
def get_data(year, month=None):

    conditions = ["YEAR(cif.inv_date) = %(year)s"]
    values = {"year": year}

    # If month is provided and not empty
    if month:
        conditions.append("MONTH(cif.inv_date) = %(month)s")
        values["month"] = month

    where_clause = " AND ".join(conditions)

    return frappe.db.sql(f"""
        SELECT
    cif.name AS invoice,
    cif.inv_date,

    YEAR(cif.inv_date) AS year,
    MONTH(cif.inv_date) AS month,

    COALESCE(pc.product_category, 'Unknown') AS category,
    COALESCE(cus.code, 'Unknown') AS customer,
    COALESCE(n.code, 'Unknown') AS notify,
    COALESCE(com.company_code, 'Unknown') AS company,
    COALESCE(cif.to_country, 'Unknown') AS country,

    cif.sales AS total_sales,
    cost.cost AS total_cost,
    (cif.sales - COALESCE(cost.cost, 0)) AS total_g_profit,
    (COALESCE(
                         COALESCE((nego.f_cost),0) + 
                         COALESCE((ref.f_cost),0)+
                         COALESCE((rec.f_cost),0)+
                         COALESCE((int_paid.f_cost),0),0)) AS total_f_cost,
   
    (cif.sales - COALESCE(cost.cost, 0)-  
                         COALESCE((nego.f_cost),0) - 
                         COALESCE((ref.f_cost),0)- 
                         COALESCE((rec.f_cost),0)-
                         COALESCE((int_paid.f_cost),0)) AS total_o_profit

FROM `tabCIF Sheet` cif
LEFT JOIN `tabCost Sheet` cost ON cost.inv_no = cif.name
LEFT JOIN `tabShipping Book` sb ON sb.name = cif.inv_no
LEFT JOIN `tabNotify` n ON n.name = sb.notify
LEFT JOIN `tabProduct Category` pc ON cif.category = pc.name
LEFT JOIN `tabCustomer` cus ON sb.customer = cus.name
LEFT JOIN `tabCompany` com ON com.name=cif.accounting_company
LEFT JOIN (SELECT 
    shipping_id,
    SUM(
        COALESCE(interest,0) +
        COALESCE(commission,0) +
        COALESCE(other_charges,0) +
        COALESCE(round_off,0)
    ) AS f_cost
FROM `tabDoc Nego Details`
GROUP BY shipping_id) nego ON nego.shipping_id= sb.name
                         
LEFT JOIN (SELECT 
    shipping_id,
    SUM(
        COALESCE(interest,0) +
        COALESCE(bank_charges,0) 
    ) AS f_cost
FROM `tabDoc Refund Details`
GROUP BY shipping_id) ref ON ref.shipping_id= sb.name

LEFT JOIN (SELECT 
    shipping_id,
    SUM(
        COALESCE(interest,0) +
        COALESCE(bank_charge,0) +
        COALESCE(foreign_charges,0) +
        COALESCE(commission,0) +
        COALESCE(postage,0) +
        COALESCE(cable_charges,0) +
        COALESCE(short_payment,0) +
        COALESCE(discrepancy_charges,0) 
    ) AS f_cost
FROM `tabDoc Received Details`
GROUP BY shipping_id) rec ON rec.shipping_id =sb.name
                         
LEFT JOIN (SELECT 
    shipping_id,
    SUM(
        COALESCE(interest,0) 
    ) AS f_cost
FROM `tabInterest Paid`
GROUP BY shipping_id) int_paid ON int_paid.shipping_id=sb.name

WHERE {where_clause}
AND COALESCE(cost.cost, 0) > 0;

""", values, as_dict=True)






import frappe
from frappe import _
from datetime import datetime, timedelta

@frappe.whitelist()
def dashboard_two(from_date, to_date, view_type, row_metric, metric_target):
    try:
        # =====================================================
        # 1. MAP THE ROW GROUP METRIC (The Matrix Row)
        # =====================================================
        row_map = {
            "row_customer": "IFNULL(cus.customer, '## Unknown Customer')",
            "row_category": "IFNULL(pcat.product_category, '## Unknown Category')",
            "row_notify": "IFNULL(noti.notify, '## Unknown Notify')",
            "row_company": "IFNULL(com.company_code, '## Unknown Company')",
            "row_supplier": "IFNULL(cost.supplier, '## Unknown Supplier')",
            "row_to_country": "IFNULL(cif.to_country, '## Unknown Destination')",
            "row_from_country": "IFNULL(cif.from_country, '## Unknown Source')"
        }
        row_field = row_map.get(row_metric, "IFNULL(cus.customer, '## Unknown Customer')")

        # =====================================================
        # 2. MAP THE VALUE METRIC EXPRESSION (The Target Value)
        # =====================================================
        metric_map = {
            "met_sales": "IFNULL(cif.sales, 0)",
            "met_purchase": "IFNULL(cost.purchase, 0)",
            "met_cost": "IFNULL(cost.cost, 0)",
            "met_freight": "IFNULL(cost.freight, 0)",
            "met_local": "IFNULL(cost.local_exp, 0)",
            "met_comm": "IFNULL(cost.commission, 0)",
            "met_profit": "(IFNULL(cif.sales, 0) - IFNULL(cost.cost, 0))"
        }
        val_expr = metric_map.get(metric_target, "IFNULL(cif.sales, 0)")

        # =====================================================
        # 3. DYNAMICALLY GENERATE PIVOT TIME COLUMNS
        # =====================================================
        start_dt = datetime.strptime(from_date, "%Y-%m-%d") if from_date else datetime(2026, 1, 1)
        end_dt = datetime.strptime(to_date, "%Y-%m-%d") if to_date else datetime(2026, 12, 31)
        
        pivot_columns = []
        loop_dt = start_dt

        if view_type == "per_quarter":
            visited_quarters = set()
            while loop_dt <= end_dt:
                yr = loop_dt.year
                qtr = (loop_dt.month - 1) // 3 + 1
                q_key = f"{yr}-Q{qtr}"
                if q_key not in visited_quarters:
                    pivot_columns.append({
                        "label": q_key,
                        "sql_cond": f"QUARTER(cif.inv_date) = {qtr} AND YEAR(cif.inv_date) = {yr}"
                    })
                    visited_quarters.add(q_key)
                loop_dt += timedelta(days=20)
                
        elif view_type == "per_year":
            while loop_dt.year <= end_dt.year:
                yr = loop_dt.year
                pivot_columns.append({
                    "label": str(yr),
                    "sql_cond": f"YEAR(cif.inv_date) = {yr}"
                })
                if loop_dt.year == end_dt.year: break
                loop_dt = datetime(yr + 1, 1, 1)
                
        else:  # "per_month" Default Fallback
            while loop_dt <= end_dt:
                m_label = loop_dt.strftime("%Y-%m")
                pivot_columns.append({
                    "label": m_label,
                    "sql_cond": f"DATE_FORMAT(cif.inv_date, '%%Y-%%m') = '{m_label}'"
                })
                next_month = loop_dt.month + 1 if loop_dt.month < 12 else 1
                next_year = loop_dt.year if loop_dt.month < 12 else loop_dt.year + 1
                loop_dt = datetime(next_year, next_month, 1)

        # =====================================================
        # 4. BUILD THE CONDITIONAL AGGREGATIONS WITH PCT HOOK
        # =====================================================
        pivot_select_chunks = []
        for col in pivot_columns:
            if metric_target == "met_profit_pct":
                # Divide-by-zero protection: returns 0 if total cost for this window is 0
                chunk = f"""
                    IFNULL(
                        (SUM(CASE WHEN {col['sql_cond']} THEN IFNULL(cif.sales, 0) ELSE 0 END) - 
                         SUM(CASE WHEN {col['sql_cond']} THEN IFNULL(cost.cost, 0) ELSE 0 END)) / 
                        NULLIF(SUM(CASE WHEN {col['sql_cond']} THEN IFNULL(cost.cost, 0) ELSE 0 END), 0) * 100, 
                        0
                    ) AS `{col['label']}`
                """
            else:
                chunk = f"SUM(CASE WHEN {col['sql_cond']} THEN {val_expr} ELSE 0 END) AS `{col['label']}`"
            
            pivot_select_chunks.append(chunk.strip())
            
        pivot_sql_string = ",\n                ".join(pivot_select_chunks)

        # Build Grand Total column calculation rules
        if metric_target == "met_profit_pct":
            grand_total_string = """
                IFNULL(
                    (SUM(IFNULL(cif.sales, 0)) - SUM(IFNULL(cost.cost, 0))) / 
                    NULLIF(SUM(IFNULL(cost.cost, 0)), 0) * 100, 
                    0
                ) AS `GRAND TOTAL`
            """
        else:
            grand_total_string = f"SUM({val_expr}) AS `GRAND TOTAL`"

        # =====================================================
        # 5. ASSEMBLE COMPREHENSIVE DYNAMIC SQL TEMPLATE
        # =====================================================
        query = f"""
            SELECT 
                {row_field} AS `{row_metric.replace("row_", "").upper()}`,
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
                    cost_s.inv_no, 
                    cost_s.name, 
                    cost_s.purchase,
                    cost_s.commission, 
                    cost_s.cost, 
                    IFNULL(sup.supplier, '## Misc Supplier') AS supplier,
                    IFNULL(exp.freight, 0) AS freight,
                    IFNULL(exp.local_exp, 0) AS local_exp,
                    IFNULL(exp.other_exp, 0) AS other_exp
                FROM `tabCost Sheet` cost_s 
                LEFT JOIN `tabSupplier` sup ON sup.name = cost_s.supplier 
                LEFT JOIN (
                    SELECT 
                        parent AS cost_id,
                        SUM(CASE WHEN expenses = 'Freight' THEN amount_usd ELSE 0 END) AS freight,
                        SUM(CASE WHEN expenses = 'Local Exp' THEN amount_usd ELSE 0 END) AS local_exp,
                        SUM(CASE WHEN expenses IN ('Inland Charges', 'Switch B/L Charges', 'Others') THEN amount_usd ELSE 0 END) AS other_exp
                    FROM `tabExpenses Cost`
                    GROUP BY parent
                ) exp ON exp.cost_id = cost_s.name
            ) cost ON cif.name = cost.inv_no
            WHERE 
                cost.cost>0
                AND (%(from_date)s IS NULL OR %(to_date)s IS NULL OR cif.inv_date BETWEEN %(from_date)s AND %(to_date)s)
            GROUP BY 
                {row_field}
            ORDER BY 
                `GRAND TOTAL` DESC
            LIMIT 300
        """

        query_params = {
            "from_date": from_date if from_date else None,
            "to_date": to_date if to_date else None
        }
        print(query)

        records = frappe.db.sql(query, query_params, as_dict=True)
        return records

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Dashboard Pure SQL Fetch Error"))
        return {"error": str(e)}