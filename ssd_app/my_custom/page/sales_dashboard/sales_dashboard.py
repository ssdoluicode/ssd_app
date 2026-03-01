import frappe


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

    -- ✅ NEW COLUMN (Sales where cost = 0)
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

    -- ✅ NEW COLUMN (Sales where cost = 0)
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
    (cif.sales - COALESCE(cost.cost, 0)) AS total_profit

FROM `tabCIF Sheet` cif
LEFT JOIN `tabCost Sheet` cost ON cost.inv_no = cif.name
LEFT JOIN `tabShipping Book` sb ON sb.name = cif.inv_no
LEFT JOIN `tabNotify` n ON n.name = sb.notify
LEFT JOIN `tabProduct Category` pc ON cif.category = pc.name
LEFT JOIN `tabCustomer` cus ON sb.customer = cus.name
LEFT JOIN `tabCompany` com ON com.name=cif.accounting_company

WHERE {where_clause}
AND COALESCE(cost.cost, 0) > 0;

    """, values, as_dict=True)