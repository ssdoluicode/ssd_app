
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt # Added flt for safer math

def set_calculated_fields(doc):
    # Fetching inv_no from Shipping Book
    invoice = frappe.db.get_value("Shipping Book", doc.inv_no, "inv_no")
    doc.custom_title = f"{doc.name} ({invoice or ''})".strip()
    doc.invoice_no = invoice
    doc.shipping_id = doc.inv_no

def final_validation(doc):
    if not doc.inv_no:
        return
    
    shi_b_data = frappe.db.get_value("Shipping Book", doc.inv_no, ["document", "bank"] , as_dict=True)
   
    bank = shi_b_data["bank"]
    shi_document = shi_b_data["document"]

    if(not bank and not doc.bank_link):
        frappe.throw(_(f"""
                ❌ <b>Bank is Blank.</b><br>
                <b>Please put Bank Name in Shipping Book or Put here<br>
            """))


    # Total received from other entries
    total_received = flt(frappe.db.sql("""
        SELECT SUM(received)
        FROM `tabDoc Received`
        WHERE inv_no = %s AND name != %s
    """, (doc.inv_no, doc.name))[0][0])

    # Current validation math
    this_entry = flt(doc.received)
    total_with_current = round(total_received + this_entry, 2)
    receivable = round(shi_document - total_received, 2)

    if total_with_current > round(shi_document, 2):
        frappe.throw(_(f"""
            ❌ <b>Received amount exceeds the receivable limit.</b>
            <br><b>Document Amount:</b> {shi_document:,.2f}
            <br><b>Total Already Received:</b> {total_received:,.2f}
            <br><b>Receivable:</b> {receivable:,.2f}
            <br><b>This Entry:</b> {this_entry:,.2f}
        """))

def set_shipping_book_bank(doc): #set bank if missing in shipping book
    shipping_bank = frappe.db.get_value("Shipping Book",doc.inv_no,"bank")

    if not shipping_bank and doc.bank_link:
        frappe.db.set_value("Shipping Book",doc.inv_no,"bank",doc.bank_link)
   


class DocReceived(Document):
    def validate(self):
        final_validation(self)
    
    def before_save(self):
        set_calculated_fields(self)
        set_shipping_book_bank(self)

@frappe.whitelist()
def get_shi_data(inv_no):
    # Fetching as dict means we MUST use shi["key"] or shi.get("key")
    shi = frappe.db.get_value(
        "Shipping Book", inv_no,
        ["bl_date", "notify", "customer", "bank", "payment_term", "term_days", "document"],
        as_dict=True
    )

    if not shi:
        return {}

    total_received = flt(frappe.db.sql("""
        SELECT SUM(received)
        FROM `tabDoc Received`
        WHERE inv_no = %s
    """, (inv_no,))[0][0])

    shi["total_received"] = round(total_received, 2)
    doc_total = flt(shi.get("document", 0))
    shi["receivable"] = round(doc_total - total_received, 2)

    # Corrected dictionary access and safe database fetching
    if shi.get("notify"):
        shi["notify_name"] = frappe.db.get_value("Notify", shi["notify"], "code")
    
    if shi.get("customer"):
        shi["customer_name"] = frappe.db.get_value("Customer", shi["customer"], "customer")
    
    if shi.get("bank"):
        shi["bank_name"] = frappe.db.get_value("Bank", shi["bank"], "bank")
        
    if shi.get("payment_term"):
        shi["payment_term_name"] = frappe.db.get_value("Payment Term", shi["payment_term"], "term_name")
        
    return shi

@frappe.whitelist()
def get_available_inv_no(doctype, txt, searchfield, start, page_len, filters):
    # Standardized query to avoid issues with hardcoded 'TT' if needed
    return frappe.db.sql(f"""
        SELECT shi.name, shi.inv_no
        FROM `tabShipping Book` AS shi
        LEFT JOIN (
            SELECT inv_no, SUM(received) AS total_received
            FROM `tabDoc Received`
            GROUP BY inv_no
        ) AS dr ON dr.inv_no = shi.name
        WHERE shi.document > 0 
        AND shi.payment_term != 'TT'
        AND (shi.inv_no LIKE %s OR shi.name LIKE %s)
        AND ROUND(shi.document - IFNULL(dr.total_received, 0), 2) > 0
        ORDER BY shi.inv_no ASC
        LIMIT %s, %s
    """, (f"%{txt}%", f"%{txt}%", start, page_len))