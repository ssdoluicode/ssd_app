import frappe

@frappe.whitelist()
def get_dashboard_data(filters=None):

    filters = frappe.parse_json(filters) or {}
    conditions = "WHERE 1 = 1"
    values = {}

    if filters.get("from_date"):
        conditions += " AND inv_date >= %(from_date)s"
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions += " AND inv_date <= %(to_date)s"
        values["to_date"] = filters["to_date"]

    # -------- KPI --------
    kpi = frappe.db.sql(f"""
        SELECT
            IFNULL(SUM(sales),0) as total_sales,
            IFNULL(SUM(document),0) as total_collection,
            IFNULL(SUM(sales - document),0) as outstanding,
            IFNULL(AVG(sales),0) as avg_invoice
        FROM `tabCIF Sheet`
        {conditions}
    """, values, as_dict=True)[0]

    # -------- Monthly Trend --------
    trend = frappe.db.sql(f"""
        SELECT DATE_FORMAT(inv_date,'%%Y-%%m') as month,
               SUM(sales) as total
        FROM `tabCIF Sheet`
        {conditions}
        GROUP BY month
        ORDER BY month
    """, values, as_dict=True)

    # -------- Top Customers --------
    top_customers = frappe.db.sql(f"""
        SELECT accounting_company as customer,
               SUM(sales) as total,
               SUM(sales - document) as outstanding
        FROM `tabCIF Sheet`
        {conditions}
        GROUP BY accounting_company
        ORDER BY total DESC
        LIMIT 10
    """, values, as_dict=True)

    # -------- Aging --------
    aging = frappe.db.sql(f"""
        SELECT
            CASE
                WHEN DATEDIFF(CURDATE(), inv_date) <= 30 THEN '0-30'
                WHEN DATEDIFF(CURDATE(), inv_date) <= 60 THEN '31-60'
                ELSE '60+'
            END as bucket,
            SUM(sales - document) as total
        FROM `tabCIF Sheet`
        {conditions}
        GROUP BY bucket
    """, values, as_dict=True)

    trend_1 = frappe.db.sql("""
        SELECT
            DATE_FORMAT(cif.inv_date,'%Y-%m') AS month,
            SUM(cif.sales) AS sales,
            SUM(cif.sales) - IFNULL(SUM(cs.total_cost),0) AS profit
        FROM `tabCIF Sheet` cif

        LEFT JOIN (
            SELECT
                inv_no,
                SUM(cost) AS total_cost
            FROM `tabCost Sheet`
            GROUP BY inv_no
        ) cs ON cs.inv_no = cif.name

        GROUP BY month
        ORDER BY month

    """, as_dict=True)


    return {
        "kpi": kpi,
        "trend": trend,
        "top_customers": top_customers,
        "aging": aging,
        "trend_1":trend_1
    }
