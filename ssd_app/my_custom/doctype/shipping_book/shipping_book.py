# # Copyright (c) 2026, SSDolui and contributors
# # For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


def validate_inv_no (doc):
    if not doc.inv_no:
        return
    dublicate= frappe.db.exists(
        "Shipping Book",
        {
            "inv_no":doc.inv_no,
            "name":["!=", doc.name]
        }
    )
    if dublicate:
        frappe.throw(
            f"Invoice No {doc.inv_no} already exits in Shipping Book"
        )


def set_value(doc): #### test on 28/4
    def r(v):
            return round(float(v or 0), 2)

    document = r(doc.document) or 0
    received = r(doc.doc_received) or 0
    nego = r(doc.doc_nego) or 0
    refund = r(doc.doc_refund) or 0

    doc.doc_receivable = r(document - received)
    doc.doc_collection = r(document - received - nego - refund)

    # Optional validations (recommended)
    if doc.doc_receivable < 0:
        frappe.throw("Received cannot exceed Document Amount")

    if doc.doc_collection < 0:
        frappe.throw("Collection cannot be negative")


class ShippingBook(Document):
    def validate(self):
        validate_inv_no(self)
        set_value(self)
        # set_all_doc_status_value()


@frappe.whitelist()
def check_related_docs(inv_id):
    return bool(frappe.db.exists("Doc Received", {"inv_no": inv_id}) or 
                frappe.db.exists("Doc Nego", {"inv_no": inv_id}) or 
                frappe.db.exists("CIF Sheet", {"inv_no": inv_id})) 





@frappe.whitelist()
def get_doc_flow(shi_id, exclude_name=None, as_on=None,):
    as_on = getdate(as_on) if as_on else None

    conditions_nego = ""
    conditions_ref = ""
    conditions_rec = ""

    if as_on:
        conditions_nego += " AND nego.nego_date <= %(as_on)s"
        conditions_ref += " AND ref.refund_date <= %(as_on)s"
        conditions_rec += " AND rec.received_date <= %(as_on)s"

    if exclude_name:
        conditions_nego += " AND nego.name != %(exclude_name)s"
        conditions_ref += " AND ref.name != %(exclude_name)s"
        conditions_rec += " AND rec.name != %(exclude_name)s"


    query = f"""
        SELECT 
            type,
            date,
            amount
        FROM (
            SELECT 
                'sales' AS type,
                shi.bl_date AS date,
                shi.document AS amount
            FROM `tabShipping Book` shi
            WHERE shi.name = %(shi_id)s

            UNION ALL
            
            SELECT 
                'nego' AS type,
                nego.nego_date AS date,
                nego.nego_amount AS amount
            FROM `tabDoc Nego` nego
            WHERE nego.shipping_id = %(shi_id)s {conditions_nego}

            UNION ALL

            SELECT 
                'refund' AS type,
                ref.refund_date AS date,
                ref.refund_amount AS amount
            FROM `tabDoc Refund` ref
            WHERE ref.shipping_id = %(shi_id)s {conditions_ref}

            UNION ALL

            SELECT 
                'received' AS type,
                rec.received_date AS date,
                rec.received AS amount
            FROM `tabDoc Received` rec
            WHERE rec.shipping_id = %(shi_id)s {conditions_rec}

        ) AS combined_data
        ORDER BY date ASC
    """

    data = frappe.db.sql(query, {
        "shi_id": shi_id,
        "as_on": as_on,
        "exclude_name": exclude_name
    }, as_dict=True)

    # -------------------------
    # VALIDATION LOGIC
    # -------------------------

    if not data:
        return data

    # Rule 1: First row must be sales
    if data[0]["type"] != "sales":
        frappe.throw("Validation Error: First entry must be SALES")

    return data



def get_doc_status_value(shi_id, this_data=None, exclude_name=None, as_on=None):
    #this_data= {"type": "nego/refund/received", "date": "2026-12-30", "amount": 500}

    def r(v):
        return round(float(v or 0), 2)

    doc_flow = list(get_doc_flow(shi_id, exclude_name, as_on))

    if this_data:
        if not this_data or "date" not in this_data or "type" not in this_data or "amount" not in this_data:
            frappe.throw("Invalid data: 'type', 'date', and 'amount' are required")

        this_data["date"] = getdate(this_data["date"])
        this_data["amount"] = r(this_data["amount"])   
        doc_flow.append(this_data)

    # Sorting
    order = {"sales": 0, "nego": 1, "refund": 2, "received": 3}
    doc_flow.sort(key=lambda d: (getdate(d["date"]), order.get(d["type"], 99)))

    seen_nego = False
  
    for row in doc_flow:
        if row["type"] == "nego":
            seen_nego = True

        if row["type"] == "refund":
            # Rule 2 & 3
            if not seen_nego:
                frappe.throw(
                    f"Validation Error: Refund found before Nego on date {row['date']}"
                )

    # Initialize
    doc_coll = doc_nego = doc_refund = doc_received = doc_receivable = 0.0

    for i in doc_flow:
        t = i["type"]
        amt = r(i["amount"])
        dt = i["date"]

        if t == "sales":
            doc_receivable = r(amt)
            doc_coll = r(amt)

        elif t == "nego":
            doc_nego = r(doc_nego + amt)
            doc_coll = r(doc_coll - amt)

            if doc_coll < 0:
                frappe.throw(f"Nego Amount exceeds Document Amount on {shi_id} at {dt}")

        elif t == "refund":
            doc_refund = r(doc_refund + amt)
            doc_nego = r(doc_nego - amt)

            if doc_nego < 0:
                frappe.throw(f"Refund exceeds Nego on {shi_id} at {dt} -- {doc_nego}")

        elif t == "received":
            doc_received = r(doc_received + amt)
            doc_receivable = r(doc_receivable - amt)

            rem_amt = amt

            # Step 1: Adjust against Nego
            if doc_nego > 0:
                adjust = min(doc_nego, rem_amt)
                adjust = r(adjust)

                doc_nego = r(doc_nego - adjust)
                rem_amt = r(rem_amt - adjust)

            # Step 2: Adjust against Refund
            if rem_amt > 0 and doc_refund > 0:
                adjust = min(doc_refund, rem_amt)
                adjust = r(adjust)

                doc_refund = r(doc_refund - adjust)
                rem_amt = r(rem_amt - adjust)

            # Step 3: Remaining reduces Coll
            if rem_amt > 0:
                doc_coll = r(doc_coll - rem_amt)

            # Validations
            if doc_coll < 0:
                frappe.throw(f"Coll Amount exceeds Document Amount on {shi_id} at {dt}")

            if doc_receivable < 0:
                frappe.throw(f"Received Amount exceeds Document Amount on {shi_id} at {dt}")

    return [
        r(doc_coll),
        r(doc_nego),
        r(doc_refund),
        r(doc_received),
        r(doc_receivable)
    ]


# def set_all_doc_status_value():
#     shi_id_list = frappe.get_all("Shipping Book", pluck="name")

#     for shi_id in shi_id_list:
#         doc_coll, doc_nego, doc_refund, doc_received, doc_receivable = get_doc_status_value(shi_id)

#         frappe.db.set_value(
#             "Shipping Book",
#             shi_id,
#             {
#                 "doc_collection": doc_coll,
#                 "doc_nego": doc_nego,
#                 "doc_refund": doc_refund,
#                 "doc_received": doc_received,
#                 "doc_receivable": doc_receivable
#             }
#         )



def set_doc_status_value(shi_id, doctype="Shipping Book", this_data=None, exclude_name=None, as_on=None):

    doc_coll, doc_nego, doc_refund, doc_received, doc_receivable = get_doc_status_value(
        shi_id, this_data, exclude_name, as_on
    )

    frappe.db.set_value(
        doctype,
        shi_id,
        {
            "doc_collection": doc_coll,
            "doc_nego": doc_nego,
            "doc_refund": doc_refund,
            "doc_received": doc_received,
            "doc_receivable": doc_receivable
        }
    )


