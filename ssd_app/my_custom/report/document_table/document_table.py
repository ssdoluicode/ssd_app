# # Copyright (c) 2025, SSDolui
# import frappe

# def execute(filters=None):
#     filters = filters or {}
#     type_filter = filters.get("type", "All")

    # -------------------------------------
    # DATE FILTER BUILDER
    # -------------------------------------
    # def date_condition(field):
    #     if filters.get("from_date") and filters.get("to_date"):
    #         return f" WHERE {field} BETWEEN %(from_date)s AND %(to_date)s "
    #     return ""

    # # -------------------------------------
    # # QUERY BLOCKS
    # # -------------------------------------

    # nego_query = f"""
    #     SELECT
    #         sb.name AS shi_id,
    #         sb.inv_no,
    #         nego.name,
    #         nego.nego_date AS date,
    #         'Nego' AS type,
    #         cus.customer,
    #         noti.code AS notify,
    #         bank.bank,
    #         IF(pt.term_name IN ('LC','DA'),
    #             CONCAT(pt.term_name,'- ',sb.term_days),
    #             pt.term_name) AS p_term,
    #         sb.document,
    #         0 AS amount,
    #         nego.nego_amount * -1 AS bank_liab,
    #         (negod.postage_charges + negod.commission +
    #          negod.other_charges + negod.round_off) AS bank_ch,
    #         negod.interest,
    #         negod.bank_amount,
    #         negod.interest_days,
    #         negod.interest_pct
    #     FROM `tabDoc Nego` nego
    #     LEFT JOIN `tabShipping Book` sb ON sb.name = nego.shipping_id
    #     LEFT JOIN `tabPayment Term` pt ON pt.name = sb.payment_term
    #     LEFT JOIN `tabCustomer` cus ON cus.name = sb.customer
    #     LEFT JOIN `tabNotify` noti ON noti.name = sb.notify
    #     LEFT JOIN `tabBank` bank ON bank.name = sb.bank
    #     LEFT JOIN `tabDoc Nego Details` negod ON nego.name = negod.inv_no
    #     {date_condition("nego.nego_date")}
    # """

    # refund_query = f"""
    #     SELECT
    #         sb.name AS shi_id,
    #         sb.inv_no,
    #         ref.name,
    #         ref.refund_date AS date,
    #         'Refund' AS type,
    #         cus.customer,
    #         noti.code AS notify,
    #         bank.bank,
    #         pt.term_name AS p_term,
    #         sb.document,
    #         0 AS amount,
    #         ref.refund_amount AS bank_liab,
    #         refd.bank_charges AS bank_ch,
    #         refd.interest,
    #         refd.bank_amount * -1 AS bank_amount,
    #         refd.interest_days,
    #         refd.interest_pct
    #     FROM `tabDoc Refund` ref
    #     LEFT JOIN `tabShipping Book` sb ON sb.name = ref.shipping_id
    #     LEFT JOIN `tabDoc Refund Details` refd ON ref.name = refd.inv_no
    #     LEFT JOIN `tabPayment Term` pt ON pt.name = sb.payment_term
    #     LEFT JOIN `tabCustomer` cus ON cus.name = sb.customer
    #     LEFT JOIN `tabNotify` noti ON noti.name = sb.notify
    #     LEFT JOIN `tabBank` bank ON bank.name = sb.bank
    #     {date_condition("ref.refund_date")}
    # """

    # received_query = f"""
    #     SELECT
    #         sb.name AS shi_id,
    #         sb.inv_no,
    #         rec.name,
    #         rec.received_date AS date,
    #         'Received' AS type,
    #         cus.customer,
    #         noti.code AS notify,
    #         bank.bank,
    #         pt.term_name AS p_term,
    #         sb.document,
    #         rec.received * -1 AS amount,
    #         recd.bank_liability AS bank_liab,
    #         (recd.bank_charge + recd.foreign_charges +
    #          recd.commission + recd.postage +
    #          recd.cable_charges + recd.short_payment +
    #          recd.discrepancy_charges) AS bank_ch,
    #         recd.interest,
    #         recd.bank_amount,
    #         recd.interest_days,
    #         recd.interest_pct
    #     FROM `tabDoc Received` rec
    #     LEFT JOIN `tabShipping Book` sb ON sb.name = rec.shipping_id
    #     LEFT JOIN `tabDoc Received Details` recd ON rec.name = recd.inv_no
    #     LEFT JOIN `tabPayment Term` pt ON pt.name = sb.payment_term
    #     LEFT JOIN `tabCustomer` cus ON cus.name = sb.customer
    #     LEFT JOIN `tabNotify` noti ON noti.name = sb.notify
    #     LEFT JOIN `tabBank` bank ON bank.name = sb.bank
    #     {date_condition("rec.received_date")}
    # """

    # interest_query = f"""
    #     SELECT
    #         sb.name AS shi_id,
    #         sb.inv_no,
    #         intp.name,
    #         intp.date AS date,
    #         'Interest' AS type,
    #         cus.customer,
    #         noti.code AS notify,
    #         bank.bank,
    #         pt.term_name AS p_term,
    #         sb.document,
    #         0 AS amount,
    #         0 AS bank_liab,
    #         0 AS bank_ch,
    #         intp.interest,
    #         intp.interest * -1 AS bank_amount,
    #         intp.interest_days,
    #         intp.interest_rate AS interest_pct
    #     FROM `tabInterest Paid` intp
    #     LEFT JOIN `tabShipping Book` sb ON sb.name = intp.shipping_id
    #     LEFT JOIN `tabPayment Term` pt ON pt.name = sb.payment_term
    #     LEFT JOIN `tabCustomer` cus ON cus.name = sb.customer
    #     LEFT JOIN `tabNotify` noti ON noti.name = sb.notify
    #     LEFT JOIN `tabBank` bank ON bank.name = sb.bank
    #     {date_condition("intp.date")}
    # """

    # # -------------------------------------
    # # 🚀 DYNAMIC UNION (KEY OPTIMIZATION)
    # # -------------------------------------
    # queries = []

    # if type_filter in ("All", "Nego"):
    #     queries.append(nego_query)

    # if type_filter in ("All", "Refund"):
    #     queries.append(refund_query)

    # if type_filter in ("All", "Received"):
    #     queries.append(received_query)

    # if type_filter in ("All", "Interest"):
    #     queries.append(interest_query)

    # union_query = "\nUNION ALL\n".join(queries)

    # # -------------------------------------
    # # FINAL QUERY
    # # -------------------------------------
    # query = f"""
    #     SELECT
    #         all_data.*,
    #         com.company_code AS com,
    #         cif.name AS cif_id
    #     FROM ({union_query}) all_data
    #     LEFT JOIN `tabCIF Sheet` cif
    #         ON cif.inv_no = all_data.shi_id
    #     LEFT JOIN `tabCompany` com
    #         ON com.name = cif.accounting_company
    #     ORDER BY all_data.date
    # """

    # data = frappe.db.sql(query, filters, as_dict=True)

import frappe
from frappe.utils import fmt_money
from datetime import date, timedelta

def execute(filters=None):

    filters = filters or {}
    type_filter = filters.get("type", "All")

    # -------------------------------------
    # DATE CONDITION
    # -------------------------------------
    def date_condition(field):
        if filters.get("from_date") and filters.get("to_date"):
            return f" WHERE {field} BETWEEN %(from_date)s AND %(to_date)s "
        return ""

    # -------------------------------------
    # NEGO
    # -------------------------------------
    nego_query = f"""
        SELECT
            sb.name AS shi_id,
            sb.inv_no,
            nego.name,
            nego.nego_date AS date,
            'Nego' AS type,

            sb.payment_term,
            sb.term_days,
            sb.customer,
            sb.notify,
            sb.bank,
            sb.document,

            0 AS amount,
            nego.nego_amount * -1 AS bank_liab,

            (negod.postage_charges +
             negod.commission +
             negod.other_charges +
             negod.round_off) AS bank_ch,

            negod.interest,
            negod.bank_amount,
            negod.interest_days,
            negod.interest_pct

        FROM `tabDoc Nego` nego
        LEFT JOIN `tabShipping Book` sb
            ON sb.name = nego.shipping_id
        LEFT JOIN `tabDoc Nego Details` negod
            ON nego.name = negod.inv_no
        {date_condition("nego.nego_date")}
    """

    # -------------------------------------
    # REFUND
    # -------------------------------------
    refund_query = f"""
        SELECT
            sb.name AS shi_id,
            sb.inv_no,
            ref.name,
            ref.refund_date AS date,
            'Refund' AS type,

            sb.payment_term,
            sb.term_days,
            sb.customer,
            sb.notify,
            sb.bank,
            sb.document,

            0 AS amount,
            ref.refund_amount AS bank_liab,
            refd.bank_charges AS bank_ch,

            refd.interest,
            refd.bank_amount * -1 AS bank_amount,
            refd.interest_days,
            refd.interest_pct

        FROM `tabDoc Refund` ref
        LEFT JOIN `tabShipping Book` sb
            ON sb.name = ref.shipping_id
        LEFT JOIN `tabDoc Refund Details` refd
            ON ref.name = refd.inv_no
        {date_condition("ref.refund_date")}
    """

    # -------------------------------------
    # RECEIVED
    # -------------------------------------
    received_query = f"""
        SELECT
            sb.name AS shi_id,
            sb.inv_no,
            rec.name,
            rec.received_date AS date,
            'Received' AS type,

            sb.payment_term,
            sb.term_days,
            sb.customer,
            sb.notify,
            sb.bank,
            sb.document,

            rec.received * -1 AS amount,
            recd.bank_liability AS bank_liab,

            (recd.bank_charge +
             recd.foreign_charges +
             recd.commission +
             recd.postage +
             recd.cable_charges +
             recd.short_payment +
             recd.discrepancy_charges) AS bank_ch,

            recd.interest,
            recd.bank_amount,
            recd.interest_days,
            recd.interest_pct

        FROM `tabDoc Received` rec
        LEFT JOIN `tabShipping Book` sb
            ON sb.name = rec.shipping_id
        LEFT JOIN `tabDoc Received Details` recd
            ON rec.name = recd.inv_no
        {date_condition("rec.received_date")}
    """

    # -------------------------------------
    # INTEREST
    # -------------------------------------
    interest_query = f"""
        SELECT
            sb.name AS shi_id,
            sb.inv_no,
            intp.name,
            intp.date AS date,
            'Interest' AS type,

            sb.payment_term,
            sb.term_days,
            sb.customer,
            sb.notify,
            sb.bank,
            sb.document,

            0 AS amount,
            0 AS bank_liab,
            0 AS bank_ch,

            intp.interest,
            intp.interest * -1 AS bank_amount,
            intp.interest_days,
            intp.interest_rate AS interest_pct

        FROM `tabInterest Paid` intp
        LEFT JOIN `tabShipping Book` sb
            ON sb.name = intp.shipping_id
        {date_condition("intp.date")}
    """

    # -------------------------------------
    # DYNAMIC UNION
    # -------------------------------------
    queries = []

    if type_filter in ("All", "Nego"):
        queries.append(nego_query)

    if type_filter in ("All", "Refund"):
        queries.append(refund_query)

    if type_filter in ("All", "Received"):
        queries.append(received_query)

    if type_filter in ("All", "Interest"):
        queries.append(interest_query)

    union_query = "\nUNION ALL\n".join(queries)

    # -------------------------------------
    # FINAL QUERY (MASTER JOIN ONCE ✅)
    # -------------------------------------
    final_query = f"""
        SELECT
            all_data.*,

            -- pt.term_name AS p_term,
            IF(pt.term_name IN ('LC','DA'),
                 CONCAT(pt.term_name,'- ',all_data.term_days),
                 pt.term_name) AS p_term,
            cus.customer,
            noti.code AS notify,
            bank.bank,

            com.company_code AS com,
            cif.name AS cif_id

        FROM ({union_query}) all_data

        LEFT JOIN `tabPayment Term` pt
            ON pt.name = all_data.payment_term

        LEFT JOIN `tabCustomer` cus
            ON cus.name = all_data.customer

        LEFT JOIN `tabNotify` noti
            ON noti.name = all_data.notify

        LEFT JOIN `tabBank` bank
            ON bank.name = all_data.bank

        LEFT JOIN `tabCIF Sheet` cif
            ON cif.inv_no = all_data.shi_id

        LEFT JOIN `tabCompany` com
            ON com.name = cif.accounting_company

        ORDER BY all_data.date
    """
    data = frappe.db.sql(final_query, filters, as_dict=True)

    

    columns = [
        {"label": "Inv No", "fieldname": "inv_no", "fieldtype": "Data", "width": 90},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
        {"label": "Com", "fieldname": "com", "fieldtype": "Data", "width": 105},
        {"label": "Notify", "fieldname": "notify", "fieldtype": "Data", "width": 220},
        {"label": "Bank", "fieldname": "bank", "fieldtype": "Data", "width": 60},
        {"label": "P Term", "fieldname": "p_term", "fieldtype": "Data", "width": 95},
        {"label": "Document", "fieldname": "document", "fieldtype": "Float", "width": 115},
        {"label": "Type", "fieldname": "type", "fieldtype": "Data", "width": 75},
        {"label": "Received", "fieldname": "amount", "fieldtype": "Float", "width": 115},
        {"label": "Bank DP/DA", "fieldname": "bank_liab", "fieldtype": "Float", "width": 120},
        {"label": "Bank Ch", "fieldname": "bank_ch", "fieldtype": "Float", "width": 85},
        {"label": "Interest", "fieldname": "interest", "fieldtype": "Float", "width": 85},
        {"label": "Bank Amount", "fieldname": "bank_amount", "fieldtype": "Float", "width": 120},
        {"label": "Int Days", "fieldname": "interest_days", "fieldtype": "Float", "width": 85},
        {"label": "Int %", "fieldname": "interest_pct", "fieldtype": "Float", "width": 60},
    ]


    return columns, data



@frappe.whitelist()
def get_finance_cost_details(inv_name):
    if not inv_name:
        return "Invalid Invoice Number"

    query = """
       
        /* ================= NEGO ================= */
        SELECT 
            'Nego' AS details,
            nego.nego_date AS date,
            1 AS sort_key,
            nego.nego_amount AS amount,
            0 AS receivable,
            nego.nego_amount AS bank_liab,
            negod.interest_days AS int_days,
            negod.interest_pct AS int_pct,
            negod.interest,
            (negod.postage_charges +
             negod.commission +
             negod.other_charges +
             negod.round_off) AS bank_ch

        FROM `tabDoc Nego` nego
        LEFT JOIN `tabDoc Nego Details` negod
            ON nego.name = negod.inv_no
        WHERE nego.shipping_id = %(shi_id)s


        UNION ALL


        /* ================= REFUND ================= */
        SELECT 
            'Refund' AS details,
            ref.refund_date AS date,
            2 AS sort_key,
            ref.refund_amount AS amount,
            0 AS receivable,
            0 AS bank_liab,
            refd.interest_days AS int_days,
            refd.interest_pct AS int_pct,
            refd.interest,
            refd.bank_charges AS bank_ch

        FROM `tabDoc Refund` ref
        LEFT JOIN `tabDoc Refund Details` refd
            ON ref.name = refd.inv_no
        WHERE ref.shipping_id = %(shi_id)s


        UNION ALL


        /* ================= RECEIVED ================= */
        SELECT 
            'Received' AS details,
            rec.received_date AS date,
            3 AS sort_key,
            rec.received AS amount,
            0 AS receivable,
            recd.bank_liability AS bank_liab,
            recd.interest_days AS int_days,
            recd.interest_pct AS int_pct,
            recd.interest,
            (recd.bank_charge +
             recd.foreign_charges +
             recd.commission +
             recd.postage +
             recd.cable_charges +
             recd.short_payment +
             recd.discrepancy_charges) AS bank_ch

        FROM `tabDoc Received` rec
        LEFT JOIN `tabDoc Received Details` recd
            ON rec.name = recd.inv_no
        WHERE rec.shipping_id = %(shi_id)s


        UNION ALL


        /* ================= INTEREST ================= */
        SELECT 
            'Interest' AS details,
            intp.date AS date,
            4 AS sort_key,
            0 AS amount,
            0 AS receivable,
            0 AS bank_liab,
            intp.interest_days AS int_days,
            intp.interest_rate AS int_pct,
            intp.interest,
            0 AS bank_ch

        FROM `tabInterest Paid` intp
        WHERE intp.shipping_id = %(shi_id)s


        ORDER BY date, sort_key
    """

    data = frappe.db.sql(
        query,
        {"shi_id": inv_name},
        as_dict=True
    )

    doc = frappe.get_doc("Shipping Book", inv_name)
    customer = frappe.get_value("Customer", doc.customer, "code")
    notify = frappe.get_value("Notify", doc.notify, "code")
    bank = frappe.get_value("Bank", doc.bank, "bank")
    payment_term_data = frappe.db.get_value("Payment Term",doc.payment_term,["term_name", "use_banking_line"],as_dict=True) or {}
    payment_term = payment_term_data.get("term_name")

    # Running totals
    receivable, bank_liab = doc.document, 0
    rows = []
    total_bank_ch=0
    total_interest=0
    for entry in data:
        typ = entry["details"]
        amt = entry["amount"] or 0
        bank_ch = entry["bank_ch"] or 0
        interest = entry["interest"] or 0
        int_days = entry["int_days"] or 0
        int_pct = entry["int_pct"] or 0
        total_bank_ch+= bank_ch
        total_interest+= interest
        if typ == "Nego":
            
            bank_liab += amt
                        
        elif typ == "Refund":
            bank_liab -= amt

        elif typ == "Received":
            receivable -= amt
            bank_liab -= amt

        rows.append(f"""
			<tr>
				<td>{typ}</td>
				<td>{entry['date']}</td>
				<td style="text-align:right;">{fmt_money(amt)}</td>
				<td style="text-align:right;">{fmt_money(receivable)}</td>
				<td style="text-align:right;">{fmt_money(max(0, bank_liab))}</td>
                <td style="text-align:right;background-color:silver;">{round(int_days, 0)}</td>
                <td style="text-align:right;background-color:silver;">{fmt_money(int_pct)}</td>
                <td style="text-align:right;background-color:silver;">{fmt_money(interest)}</td>
				<td style="text-align:right;background-color:silver;">{fmt_money(bank_ch)}</td>
			</tr>
		""")

    finance_cost= total_bank_ch + total_interest
	# Build final HTML
    html = f"""
	<div style="bmargin-bottom: 12px; background-color: #f9f9f9; padding: 8px 12px;  border-radius: 6px; 
	box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
    <table style="width:100%; font-size:13px; margin-bottom:0;">
			<tr><td><b>Invoice Date:</b> {doc.bl_date}</td><td><b>Customer:</b> {customer}</td><td><b>Notify:</b> {notify}</td></tr>
			<tr><td><b>Bank:</b> {bank}</td><td><b>Payment Term:</b> {payment_term}{' - '+str(doc.term_days) if payment_term in ['LC','DA'] else ''}</td> <td><b>Finance Cost:</b> {finance_cost}</td></tr>
		</table>
	</div>
	<table class="table table-bordered" style="font-size:14px; border:1px solid #ddd;">
		<thead style="background-color: #f1f1f1;">
			<tr>
				<th style="width:10%; text-align:center;">Type</th>
				<th style="width:15%; text-align:center;">Date</th>
				<th style="width:10%;text-align:center;">Amount</th>
				<th style="width:10%;text-align:center;">Receivable</th>
				<th style="width:10%;text-align:center;">Bank Liability</th>
                <th style="width:10%;text-align:center;">Int Dys</th>
                <th style="width:10%;text-align:center;">Int %</th>
                <th style="width:10%;text-align:center;">Interest</th>
				<th style="width:10%;text-align:center;">Bank Charges</th>
			</tr>
		</thead>
		<tbody style="border-top:1px solid #ddd;">

			{''.join(rows)}
            <tr style="font-weight:bold; background-color:#f5f5f5;">
                <td colspan="7" style="text-align:right;">TOTAL</td>
                <td style="text-align:right;">
                    {fmt_money(total_interest)}
                </td>
                <td style="text-align:right;">
                    {fmt_money(total_bank_ch)}
                </td>
            </tr>
		</tbody>
	</table>
	<div style="text-align:right; margin-top:12px;padding:8px; border-top:1px solid #eee;">
	</div>


	"""
    return html
