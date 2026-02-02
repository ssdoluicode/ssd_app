import frappe
def execute(filters=None):
    filters = filters or {}

    query = """
SELECT 
    t.name,
    t.date,
    t.inv_no,
    t.customer,
    t.notify,
    t.sales,
    t.document,
    t.cc,
    t.note,
    t.dev_note,
    SUM(t.cc) OVER (
        PARTITION BY t.customer
        ORDER BY t.date, t.inv_no
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS balance
FROM (
    /* =========================
       Opening Balance
       ========================= */
    SELECT 
        '' AS name,
        %(from_date)s AS date,
        '' AS inv_no,
        %(customer)s AS customer,
        '' AS notify,
        NULL AS sales,
        NULL AS document,
        SUM(amount) AS cc,
        'Opening Balance' AS note,
        'opening' AS dev_note
    FROM (
        -- CIF opening
        SELECT 
            sb.customer,
            SUM(cif.cc) AS amount
        FROM `tabCIF Sheet` cif
        INNER JOIN `tabShipping Book` sb
            ON sb.name = cif.inv_no
        WHERE cif.cc != 0
          AND sb.customer = %(customer)s
          AND cif.inv_date < %(from_date)s
        GROUP BY sb.customer

        UNION ALL

        -- CC Received opening
        SELECT 
            customer,
            SUM(amount_usd) * -1 AS amount
        FROM `tabCC Received`
        WHERE customer = %(customer)s
          AND date < %(from_date)s
        GROUP BY customer
    ) opening
    GROUP BY customer

    UNION ALL

    /* =========================
       CIF Sheet Entries
       ========================= */
    SELECT
        cif.name,
        cif.inv_date AS date,
        sb.inv_no AS inv_no,
        sb.customer,
        noti.notify,
        cif.sales,
        sb.document,
        cif.cc,
        '' AS note,
        'cif' AS dev_note
    FROM `tabCIF Sheet` cif
    LEFT JOIN `tabShipping Book` sb
        ON sb.name = cif.inv_no
    LEFT JOIN tabNotify noti ON sb.notify = noti.name
    WHERE cif.cc != 0
      AND (%(customer)s IS NULL OR sb.customer = %(customer)s)
      AND (%(as_on)s IS NULL OR cif.inv_date <= %(as_on)s)
      AND (%(from_date)s IS NULL OR cif.inv_date >= %(from_date)s)

    UNION ALL

    /* =========================
       CC Received Entries
       ========================= */
    SELECT
        rec.name,
        rec.date,
        '' AS inv_no,
        rec.customer,
        '' AS notify,
        NULL AS sales,
        NULL AS document,
        rec.amount_usd * -1 AS cc,
        rec.note,
        'rec' AS dev_note
    FROM `tabCC Received` rec
    WHERE (%(customer)s IS NULL OR rec.customer = %(customer)s)
      AND (%(as_on)s IS NULL OR rec.date <= %(as_on)s)
      AND (%(from_date)s IS NULL OR rec.date >= %(from_date)s)
) t
ORDER BY t.date, t.inv_no;

"""


    result = frappe.db.sql(query, filters, as_dict=True)

    columns = [
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 120},
        {"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 150},
        {"label": "Sales", "fieldname": "sales", "fieldtype": "Float", "width": 120},
        {"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 120},
        {"label": "CC", "fieldname": "cc", "fieldtype": "Float", "width": 120},
        {"label": "Balance", "fieldname": "balance", "fieldtype": "Float", "width": 120},
        {"label": "Narration", "fieldname": "note", "fieldtype": "Data", "width": 250},
    ]

    if not filters.get("customer"):
        columns.insert(3, {
            "label": "Customer",
            "fieldname": "customer",
            "fieldtype": "Data",
            "width": 150
        })

    return columns, result
