import frappe

def execute(filters=None):
    filters = frappe._dict(filters or {})

    limit_clause = ""
    if filters.get("limit"):
        try:
            limit = int(filters.get("limit"))
            if limit > 0:
                limit_clause = f" LIMIT {limit}"
        except:
            pass

    conditions = ""
    if filters.get("from_date") and filters.get("to_date"):
        conditions += f" AND cif.inv_date BETWEEN '{filters.get('from_date')}' AND '{filters.get('to_date')}'"

    query = f"""
    SELECT 
    cif.inv_no, cif.inv_date, com.company_code AS company, 
    pcat.product_category AS category, cus.customer AS customer, 
    noti.notify AS notify, cost.supplier, 
    cif.gross_sales, cif.handling_charges, cif.sales, cif.document, cif.cc, 
    cost.purchase, 
    cost.freight,
    cost.local_exp,
    cost.other_exp,
    cost.commission, cost.cost, cost.profit, cost.profit_pct,
    IF(cif.payment_term IN ('LC', 'DA'), CONCAT(cif.payment_term, '- ', cif.term_days), cif.payment_term) AS p_term,
    cif.from_country AS f_country, lport.port AS l_port, 
    cif.to_country AS t_country, dport.port AS d_port
FROM `tabCIF Sheet` cif
LEFT JOIN `tabCompany` com ON cif.accounting_company = com.name
LEFT JOIN `tabProduct Category` pcat ON cif.category = pcat.name
LEFT JOIN `tabCustomer` cus ON cif.customer = cus.name
LEFT JOIN `tabNotify` noti ON cif.notify = noti.name
LEFT JOIN `tabBank` bank ON cif.bank = bank.name
LEFT JOIN `tabPort` lport ON cif.load_port = lport.name
LEFT JOIN `tabPort` dport ON cif.destination_port = dport.name
LEFT JOIN (
    SELECT 
        cost_s.inv_no, 
        cost_s.name, 
        cost_s.purchase,
        cost_s.commission, 
        cost_s.cost, 
        cost_s.profit, 
        cost_s.profit_pct, 
        IFNULL(sup.supplier, '## Misc Supplier') AS supplier,
        IFNULL(exp.freight, 0) AS freight,
        IFNULL(exp.local_exp, 0) AS local_exp,
        IFNULL(exp.other_exp, 0) AS other_exp
    FROM 
        `tabCost Sheet` cost_s 
    LEFT JOIN 
        `tabSupplier` sup 
        ON sup.name = cost_s.supplier 
    LEFT JOIN (
        SELECT 
            parent AS cost_id,
            SUM(CASE WHEN expenses = 'Freight' THEN amount_usd ELSE 0 END) AS freight,
            SUM(CASE WHEN expenses = 'Local Exp' THEN amount_usd ELSE 0 END) AS local_exp,
            SUM(CASE WHEN expenses IN ('Inland Charges', 'Switch B/L Charges', 'Others') THEN amount_usd ELSE 0 END) AS other_exp
        FROM 
            `tabExpenses Cost`
        GROUP BY 
            parent
    ) exp 
        ON exp.cost_id = cost_s.name
) cost ON cif.name = cost.inv_no

    WHERE 1=1 {conditions} {limit_clause}
    """

    data = frappe.db.sql(query, as_dict=1)

    columns = [
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
        {"label": "Inv Date", "fieldname": "inv_date", "fieldtype": "Date", "width": 110},
        {"label": "Com", "fieldname": "company", "fieldtype": "Data", "width": 110},
        {"label": "Category", "fieldname": "category", "fieldtype": "Data", "width": 110},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Data", "width": 110},
        {"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 110},
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Data", "width": 110},
        {"label": "G Sales", "fieldname": "gross_sales", "fieldtype": "Float", "width": 110},
        {"label": "Handling", "fieldname": "handling_charges", "fieldtype": "Float", "width": 90},
        {"label": "Sales", "fieldname": "sales", "fieldtype": "Float", "width": 110},
        {"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 110},
        {"label": "CC", "fieldname": "cc", "fieldtype": "Float", "width": 110},
        {"label": "Purchase", "fieldname": "purchase", "fieldtype": "Float", "width": 110},
        {"label": "Freight", "fieldname": "freight", "fieldtype": "Float", "width": 110},
        {"label": "Local Exp", "fieldname": "local_exp", "fieldtype": "Float", "width": 110},
        {"label": "Other Exp", "fieldname": "other_exp", "fieldtype": "Float", "width": 110},
        {"label": "Comm", "fieldname": "commission", "fieldtype": "Float", "width": 110},
        {"label": "Cost", "fieldname": "cost", "fieldtype": "Float", "width": 110},
        {"label": "Profit", "fieldname": "profit", "fieldtype": "Float", "width": 110},
        {"label": "Profit %", "fieldname": "profit_pct", "fieldtype": "Percent", "width": 90},
        {"label": "P Term", "fieldname": "p_term", "fieldtype": "Data", "width": 90},
        {"label": "F Country", "fieldname": "f_country", "fieldtype": "Data", "width": 90},
        {"label": "L Port", "fieldname": "l_port", "fieldtype": "Data", "width": 90},
        {"label": "T Country", "fieldname": "t_country", "fieldtype": "Data", "width": 90},
        {"label": "D Port", "fieldname": "d_port", "fieldtype": "Data", "width": 90},
    ]

    return columns, data
