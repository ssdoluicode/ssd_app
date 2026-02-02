# Copyright (c) 2025, SSDolui and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	customer = filters.get("customer", "")
	from_date = filters.get('from_date')
	
	data = frappe.db.sql("""
        SELECT
            combined.*,
            CASE 
                WHEN combined.note NOT IN ('product','total')
                THEN SUM(IFNULL(combined.cc,0))
                    OVER (
                        PARTITION BY combined.cus
                        ORDER BY combined.i_date, combined.idex
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    )
                ELSE NULL
            END AS balance
        FROM (

            /* ======================================================
            OPENING BALANCE
            ====================================================== */
            SELECT 
                -1 AS idex,
                '' AS inv_no,
                NULL AS name,
                t.cus,
                '' AS i_inv_no,
                %(from_date)s AS date,
                %(from_date)s AS i_date,
                'Opening Balance' AS details,
                NULL AS qty,
                NULL AS rate,
                NULL AS curr,
                NULL AS ex_rate,
                NULL AS total,
                NULL AS g_sales,
                NULL AS added_cost,
                NULL AS handling_charges,
                NULL AS sales,
                NULL AS document,
                SUM(t.amount) AS cc,
                '' AS notify,
                'opening' AS note
            FROM (
                /* CIF CC before from_date */
                SELECT 
                    sb.customer AS cus,
                    SUM(cif.cc) AS amount
                FROM `tabCIF Sheet` cif
                LEFT JOIN `tabShipping Book` sb ON sb.name = cif.inv_no
                WHERE cif.cc != 0
                AND sb.customer = %(customer)s
                AND cif.inv_date < %(from_date)s
                GROUP BY sb.customer

                UNION ALL

                /* CC Received before from_date */
                SELECT 
                    ccr.customer AS cus,
                    SUM(ccr.amount_usd) * -1 AS amount
                FROM `tabCC Received` ccr
                WHERE ccr.customer = %(customer)s
                AND ccr.date < %(from_date)s
                GROUP BY ccr.customer
            ) t
            GROUP BY t.cus


            UNION ALL


            /* ======================================================
            CIF SHEET SUMMARY
            ====================================================== */
            SELECT 
                CAST(SUBSTRING_INDEX(cif.name, '-', -1) AS DECIMAL(20,2)) + 1000000 AS idex,
                sb.inv_no,
                cif.name,
                sb.customer AS cus,
                cif.inv_no AS i_inv_no,
                cif.inv_date AS date,
                cif.inv_date AS i_date,
                pcat.product_category AS details,
                NULL AS qty,
                NULL AS rate,
                NULL AS curr,
                NULL AS ex_rate,
                NULL AS total,
                cif.gross_sales AS g_sales,
                (cif.sales - cif.gross_sales - cif.handling_charges) AS added_cost,
                cif.handling_charges,
                cif.sales,
                cif.document,
                cif.cc,
                noti.code AS notify,
                'cif' AS note
            FROM `tabCIF Sheet` cif
            LEFT JOIN `tabShipping Book` sb ON sb.name = cif.inv_no
            LEFT JOIN `tabNotify` noti ON noti.name = sb.notify
            LEFT JOIN `tabProduct Category` pcat ON pcat.name = cif.category
            WHERE cif.inv_date >= %(from_date)s


            UNION ALL


            /* ======================================================
            CC RECEIVED
            ====================================================== */
            SELECT 
                CAST(SUBSTRING_INDEX(ccr.name, '-', -1) AS DECIMAL(20,2)) AS idex,
                '' AS inv_no,
                ccr.name,
                ccr.customer AS cus,
                '' AS i_inv_no,
                ccr.date,
                ccr.date AS i_date,
                ccr.note AS details,
                NULL AS qty,
                NULL AS rate,
                NULL AS curr,
                NULL AS ex_rate,
                NULL AS total,
                NULL AS g_sales,
                NULL AS added_cost,
                NULL AS handling_charges,
                NULL AS sales,
                NULL AS document,
                ccr.amount_usd * -1 AS cc,
                '' AS notify,
                'received' AS note
            FROM `tabCC Received` ccr
            WHERE ccr.date >= %(from_date)s


            UNION ALL


            /* ======================================================
            PRODUCT DETAILS
            ====================================================== */
            SELECT 
                CAST(SUBSTRING_INDEX(cif.name, '-', -1) AS DECIMAL(20,2)) + 1000000.1 AS idex,
                '' AS inv_no,
                cif.name,
                sb.customer AS cus,
                cif.inv_no AS i_inv_no,
                NULL AS date,
                cif.inv_date AS i_date,
                pro.product AS details,
                pcif.qty,
                pcif.rate,
                pcif.currency AS curr,
                pcif.ex_rate AS ex_rate,
                pcif.gross_usd AS total,
                NULL AS g_sales,
                NULL AS added_cost,
                NULL AS handling_charges,
                NULL AS sales,
                NULL AS document,
                NULL AS cc,
                '' AS notify,
                'product' AS note
            FROM `tabProduct CIF` pcif
            LEFT JOIN `tabCIF Sheet` cif ON cif.name = pcif.parent
            LEFT JOIN `tabShipping Book` sb ON sb.name = cif.inv_no
            LEFT JOIN `tabProduct` pro ON pro.name = pcif.product
            WHERE cif.inv_date >= %(from_date)s


            UNION ALL


            /* ======================================================
            PRODUCT TOTALS
            ====================================================== */
            SELECT 
                CAST(SUBSTRING_INDEX(cif.name, '-', -1) AS DECIMAL(20,2)) + 1000000.2 AS idex,
                '' AS inv_no,
                cif.name,
                sb.customer AS cus,
                sb.inv_no AS i_inv_no,
                NULL AS date,
                cif.inv_date AS i_date,
                NULL AS details,
                SUM(cifp.qty) AS qty,
                NULL AS rate,
                NULL AS curr,
                NULL AS ex_rate,
                SUM(cifp.gross_usd) AS total,
                NULL AS g_sales,
                NULL AS added_cost,
                NULL AS handling_charges,
                NULL AS sales,
                NULL AS document,
                NULL AS cc,
                '' AS notify,
                'total' AS note
            FROM `tabProduct CIF` cifp
            LEFT JOIN `tabCIF Sheet` cif ON cif.name = cifp.parent
            LEFT JOIN `tabShipping Book` sb ON sb.name = cif.inv_no
            WHERE cif.inv_date >= %(from_date)s
            GROUP BY cifp.parent

        ) combined
        WHERE combined.cus = %(customer)s
        ORDER BY 
            combined.i_date IS NULL,
            combined.i_date,
            combined.idex
    """, {
        "from_date": from_date,
        "customer": customer
    }, as_dict=True)




	columns= [
		# {"label": "Index", "fieldname": "note", "fieldtype": "Data", "width": 85},
		# {"label": "Customer", "fieldname": "cus", "fieldtype": "Data", "width": 85},
		{"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 85},
		{"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": "Details", "fieldname": "details", "fieldtype": "Data", "width": 280},
		{"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 110},
		{"label": "Rate", "fieldname": "rate","fieldtype": "Currency", "options": "curr", "width": 90},
		{"label": "Ex Rate", "fieldname": "ex_rate", "fieldtype": "Float", "width": 80},
		{"label": "Total", "fieldname": "total", "fieldtype": "Float", "width": 110},
		{"label": "G Sales", "fieldname": "g_sales", "fieldtype": "Float", "width": 110},
		{"label": "Added Cost", "fieldname": "added_cost", "fieldtype": "Float", "width": 110},
		{"label": "Handling", "fieldname": "handling_charges", "fieldtype": "Float", "width": 110},
		{"label": "Sales", "fieldname": "sales", "fieldtype": "Float", "width": 110},
		{"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 110},
		{"label": "CC", "fieldname": "cc", "fieldtype": "Float", "width": 110},
		{"label": "Balance", "fieldname": "balance", "fieldtype": "Float", "width": 110},
		{"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 110},
		]
	

	return columns, data
