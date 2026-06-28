import pandas as pd
from xml.sax.saxutils import escape

class GenerateTallyXML:
    USD_RATE = 30  # Default TWD Exchange Rate 

    COMPANY_MAP = {
        2: "Uniexcel Ltd - Twn.",
        3: "Tun Wa Industrial Co Ltd.",
        8: "Grand Dignity Industrial Co.Ltd.",
        9: "Uniexcel China Ltd."
    }

    def __init__(self, company: int):

        if company not in self.COMPANY_MAP:
            raise ValueError(
                f"Invalid company code: {company}. "
                f"Valid codes are: {list(self.COMPANY_MAP.keys())}"
            )

        self.company = self.COMPANY_MAP[company]

    # ---------- Utilities ----------
    @staticmethod
    def escape_xml(val) -> str:
        """Handles special characters like &, <, > for Tally compatibility"""
        if pd.isna(val) or val is None:
            return ""
        # escape() converts & to &amp;, < to &lt;, > to &gt;
        return escape(str(val).strip())
    
    @staticmethod
    def clean_amount(val) -> float:
        if pd.isna(val):
            return 0.0
        return float(str(val).replace(",", "").strip())

    @staticmethod
    def fmt_date(d) -> str:
        return pd.to_datetime(d).strftime("%Y%m%d")

    def amt_xml(self, usd: float, sign: int = 1) -> str:
        """
        sign =  1 -> Debit
        sign = -1 -> Credit
        """
        usd_val = usd * sign
        nt_val = usd * self.USD_RATE * sign
        return f"USD {usd_val:.2f} @ NT {self.USD_RATE}/USD = NT {nt_val:.3f}"

        # ---------- Universal Ledger Entry ----------
    def ledger_entry(
            self,
            ledger: str,
            amount: float,
            bill_details: list | None = None,   # [{name, type, amount}]
            is_party: bool = False,
            cost_centers: list | None = None # working on this
        ) -> str:
        """
        Universal Tally Ledger Entry
        bill_details example:
        [
            {"name": "INV-001", "type": "Agst Ref", "amount": 500},
            {"name": "INV-002", "type": "Agst Ref", "amount": 500}
        ]
        """

        sign = 1 if amount < 0 else -1
        deemed = "No" if amount < 0 else "Yes"
        abs_amount=abs(amount)

        # -------------------------
        # Bill Allocations
        # -------------------------
        bill_xml = ""

        if bill_details:
            for bill in bill_details:
                bill_amt = bill.get("amount", abs_amount)
                sign = 1 if bill_amt < 0 else -1
                abs_bill_amt= abs(bill_amt)
                bill_xml += f"""
                   <BILLALLOCATIONS.LIST>
                    <NAME>{bill["name"]}</NAME>
                    <BILLTYPE>{bill["type"]}</BILLTYPE>
                    <AMOUNT>{self.amt_xml(abs_bill_amt, sign)}</AMOUNT>
                   </BILLALLOCATIONS.LIST>
                    """
        # -------------------------
        # Cost Center Allocations # working on this
        # -------------------------
        cost_center_xml = ""

        if cost_centers:
            for cc in cost_centers:
                cc_amt = cc.get("amount", abs_amount)
                cc_sign = 1 if cc_amt < 0 else -1
                abs_cc_amt = abs(cc_amt)
                nt_amount= round(abs_cc_amt * cc_sign * self.USD_RATE,2)


                cost_center_xml += f"""
                <CATEGORYALLOCATIONS.LIST>
                    <CATEGORY>Primary Cost Category</CATEGORY>
                    <ISDEEMEDPOSITIVE>{"No" if cc_amt < 0 else "Yes"}</ISDEEMEDPOSITIVE>
                    <COSTCENTREALLOCATIONS.LIST>
                        <NAME>{cc["name"]}</NAME>
                        <AMOUNT>{nt_amount}</AMOUNT>
                    </COSTCENTREALLOCATIONS.LIST>
                </CATEGORYALLOCATIONS.LIST>
                """

        # -------------------------
        # Ledger Entry XML
        # -------------------------
        return f"""
          <ALLLEDGERENTRIES.LIST>
           <LEDGERNAME>{ledger}</LEDGERNAME>
           <ISDEEMEDPOSITIVE>{deemed}</ISDEEMEDPOSITIVE>
           {'<ISPARTYLEDGER>Yes</ISPARTYLEDGER>' if is_party else ''}
           <AMOUNT>{self.amt_xml(abs_amount, sign)}</AMOUNT>
           {bill_xml}
           {cost_center_xml}
          </ALLLEDGERENTRIES.LIST>
        """

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # ---------- Function for Generate Sales Entry XML---------- 
    def generate_sales_entry_xml(self, df: pd.DataFrame) -> None:
        vouchers_xml = []
    
        for i, r in df.iterrows():
            # String -----------------------------
            inv_no = self.escape_xml(r["inv_no"])
            notify = self.escape_xml(r["notify"])
            customer = self.escape_xml(r["customer"])
            customer_doc = self.escape_xml(r["customer_doc"])
            customer_cc = self.escape_xml(r["customer_cc"])
            sales_head = self.escape_xml(r["sales_head"])
            p_term = self.escape_xml(r["p_term"])

            # Date -----------------------------
            date = self.fmt_date(r["inv_date"])
            
            # Amounts -----------------------------
            sales = round(self.clean_amount(r["sales"]), 2)
            document = round(self.clean_amount(r["document"]), 2)
            cc = round(self.clean_amount(r["cc"]), 2)
            dir_to_sup = self.clean_amount(r["dir_to_sup"])

             # 🔒 Financial validation
            amount_tally = sales + document + cc
            if round(amount_tally, 2) != 0:
                raise ValueError(
                    f"❌ Amount mismatch at row {i+1} (Invoice {inv_no})"
                )
    
            # -----------------------------
            # Build Voucher XML
            # -----------------------------
            voucher = f"""
                        <TALLYMESSAGE>
                         <VOUCHER ACTION="Create" VCHTYPE="Sales">
                          <DATE>{date}</DATE>
                          <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
                          <VOUCHERNUMBER>{inv_no}</VOUCHERNUMBER>
                          <NARRATION>{notify}-- USD{sales}-- Payment Term {p_term}-- {customer}</NARRATION>
                        """
            if(dir_to_sup==0):
                # Dr Customer Document Amount:
                if(document > 0):
                    bill_details=[{"name": inv_no, "type": "New Ref", "amount": document}]
                    voucher += self.ledger_entry(customer_doc, document, is_party=True, bill_details=bill_details)
                else:
                    bill_details=[{"name": inv_no, "type": "New Ref", "amount": 1}]
                    voucher += self.ledger_entry("Direct TT", 1, is_party=True, bill_details=bill_details)

                # Cr Sales Amount:    
                cost_center_details=[{"name": inv_no, "amount": sales}]
                voucher += self.ledger_entry(ledger=sales_head,amount=sales, cost_centers= cost_center_details)
                    
                # Dr/Cr Customer CC Amount:
                voucher += self.ledger_entry(ledger=customer_cc, amount=cc, is_party=True)

                # Cr "Bank Charges - EB" if Document=0
                if (document == 0):
                    voucher += self.ledger_entry(ledger="Bank Charges - EB",amount=-1)
            
            else:
                continue

        
            voucher += """
                     </VOUCHER>
                    </TALLYMESSAGE>
                    """
            vouchers_xml.append(voucher)
    
    
        # -----------------------------
        # Write Final XML
        # -----------------------------
        final_xml = f"""<ENVELOPE>
                 <HEADER>
                  <TALLYREQUEST>Import Data</TALLYREQUEST>
                 </HEADER>
                 <BODY>
                  <IMPORTDATA>
                   <REQUESTDESC>
                    <REPORTNAME>Vouchers</REPORTNAME>
                    <STATICVARIABLES>
                     <SVCURRENTCOMPANY>{self.company}</SVCURRENTCOMPANY>
                    </STATICVARIABLES>
                   </REQUESTDESC>
                   <REQUESTDATA>
                {''.join(vouchers_xml)}
                   </REQUESTDATA>
                  </IMPORTDATA>
                 </BODY>
                </ENVELOPE>
                """
        return final_xml

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # ---------- Function for Generate Sales Entry XML---------- 
    def generate_purchase_entry_xml(self, df: pd.DataFrame) -> None:
        vouchers_xml = []
    
        for i, r in df.iterrows():
            # String -----------------------------
            sr_no = self.escape_xml(r["sr_no"])
            inv_no = self.escape_xml(r["inv_no"])
            supplier_name = self.escape_xml(r["supplier_name"])
            purchase_head = self.escape_xml(r["purchase_head"])
            # Date -----------------------------
            date = self.fmt_date(r["inv_date"])
            
            # Amounts -----------------------------
            purchase = round(self.clean_amount(r["pur_amt"]), 2)
            supplier = round(self.clean_amount(r["sup_amt"]), 2)

             # 🔒 Financial validation
            amount_tally = purchase + supplier
            if round(amount_tally, 2) != 0:
                raise ValueError(
                    f"❌ Amount mismatch at row {i+1} (Invoice {inv_no})"
                )
    
            # -----------------------------
            # Build Voucher XML
            # -----------------------------
            voucher = f"""
                        <TALLYMESSAGE>
                         <VOUCHER ACTION="Create" VCHTYPE="Purchase">
                          <DATE>{date}</DATE>
                          <VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME>
                          <VOUCHERNUMBER>{inv_no}</VOUCHERNUMBER>
                          <NARRATION>Being purchase booked-- {supplier_name}-- Inv no {inv_no}-- Serial No {sr_no}</NARRATION>
                        """
   
            bill_details=[{"name": inv_no, "type": "New Ref", "amount": supplier}]
            voucher += self.ledger_entry(supplier_name, supplier, is_party=True, bill_details=bill_details)

            cost_center_details=[{"name": inv_no, "amount": purchase}]
            voucher += self.ledger_entry(ledger=purchase_head,amount=purchase, cost_centers= cost_center_details)
                       
            voucher += """
                     </VOUCHER>
                    </TALLYMESSAGE>
                    """
            vouchers_xml.append(voucher)
    
    
        # -----------------------------
        # Write Final XML
        # -----------------------------
        final_xml = f"""<ENVELOPE>
                 <HEADER>
                  <TALLYREQUEST>Import Data</TALLYREQUEST>
                 </HEADER>
                 <BODY>
                  <IMPORTDATA>
                   <REQUESTDESC>
                    <REPORTNAME>Vouchers</REPORTNAME>
                    <STATICVARIABLES>
                     <SVCURRENTCOMPANY>{self.company}</SVCURRENTCOMPANY>
                    </STATICVARIABLES>
                   </REQUESTDESC>
                   <REQUESTDATA>
                {''.join(vouchers_xml)}
                   </REQUESTDATA>
                  </IMPORTDATA>
                 </BODY>
                </ENVELOPE>
                """
        return final_xml

    
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # ---------- Function for Generate Doc Received Entry XML---------- 
    def generate_doc_nego_xml(self, df: pd.DataFrame) -> None:
        vouchers_xml = []
    
        for i, r in df.iterrows():
            # String -----------------------------
            bank_dpda = self.escape_xml(r["bank_dpda"])
            notify_party = self.escape_xml(r["notify_party"])
            ref_no = self.escape_xml(r["ref_no"])
            bank_name = self.escape_xml(r["bank_name"])
            inv_no = self.escape_xml(r["inv_no"])

            # Date -----------------------------
            date = self.fmt_date(r["date"])
            
            # Amounts -----------------------------
            nego_amount = self.clean_amount(r["nego_amount"])
            bank_charge = self.clean_amount(r["bank_charge"])
            interest = self.clean_amount(r["interest"])
            bank_amount = self.clean_amount(r["bank_amount"])

             # 🔒 Financial validation
            amount_tally = round(nego_amount + bank_charge + interest + bank_amount, 2)
            if round(amount_tally, 2) != 0:
                raise ValueError(
                    f"❌ Amount mismatch at row {i+1} (Invoice {inv_no})"
                )
    
            # -----------------------------
            # Build Voucher XML
            # -----------------------------
            voucher = f"""
                        <TALLYMESSAGE>
                         <VOUCHER ACTION="Create" VCHTYPE="Receipt">
                          <DATE>{date}</DATE>
                          <VOUCHERTYPENAME>Receipt</VOUCHERTYPENAME>
                          <VOUCHERNUMBER>{ref_no}</VOUCHERNUMBER>
                          <NARRATION>Being inv no {inv_no} drawn on {notify_party} now negotiated from bank.</NARRATION>
                        """

             # Cr Bank bank iability (DPDA)
            bill_details=[{"name": inv_no, "type": "New Ref", "amount": nego_amount}]
            voucher += self.ledger_entry(bank_dpda, nego_amount, is_party=True, bill_details=bill_details)

             # Dr Bank Charge:
            if bank_charge != 0:
                voucher += self.ledger_entry(ledger="Bank Charges - EB",amount=bank_charge)
                
            # Dr Interest:    
            if interest != 0:
                voucher += self.ledger_entry(ledger="Interest Paid - (EB-DP-DA)",amount=interest)
                
            # Dr bank_amount:
            voucher += self.ledger_entry(ledger=bank_name,amount=bank_amount,is_party=True)
        
            voucher += """
                     </VOUCHER>
                    </TALLYMESSAGE>
                    """
            vouchers_xml.append(voucher)
    
    
        # -----------------------------
        # Write Final XML
        # -----------------------------
        final_xml = f"""<ENVELOPE>
                 <HEADER>
                  <TALLYREQUEST>Import Data</TALLYREQUEST>
                 </HEADER>
                 <BODY>
                  <IMPORTDATA>
                   <REQUESTDESC>
                    <REPORTNAME>Vouchers</REPORTNAME>
                    <STATICVARIABLES>
                     <SVCURRENTCOMPANY>{self.company}</SVCURRENTCOMPANY>
                    </STATICVARIABLES>
                   </REQUESTDESC>
                   <REQUESTDATA>
                {''.join(vouchers_xml)}
                   </REQUESTDATA>
                  </IMPORTDATA>
                 </BODY>
                </ENVELOPE>
                """
        return final_xml

    
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # ---------- Function for Generate Doc Refund XML----------
    def generate_doc_ref_xml(self, df: pd.DataFrame) -> None:
    
        vouchers_xml = []
    
        for i, r in df.iterrows():
             # String -----------------------------
            inv_no = str(r["inv_no"]).strip()
            ref_no = str(r["ref_no"]).strip()
            bank_name = str(r["bank_name"]).strip()
            bank_dpda = str(r["bank_dpda"]).strip()
            notify_party = str(r["notify_party"]).strip()
            
            # Date -----------------------------
            date = self.fmt_date(r["date"])

            # Amounts -----------------------------
            ref_amt = self.clean_amount(r["ref_amount"])
            interest = self.clean_amount(r.get("interest", 0))
            bank_charge = self.clean_amount(r.get("bank_charge", 0))
            bank_amount = self.clean_amount(r["bank_amount"])
    
            # 🔒 Financial validation
            amount_tally = round(ref_amt + interest + bank_charge + bank_amount, 2)
            if round(amount_tally, 2) != 0:
                raise ValueError(
                    f"❌ Amount mismatch at row {i+1} (Invoice {inv_no})"
                )
    
            # -----------------------------
            # Build Voucher XML
            # -----------------------------
            voucher = f"""
                        <TALLYMESSAGE>
                         <VOUCHER ACTION="Create" VCHTYPE="Payment">
                          <DATE>{date}</DATE>
                          <VOUCHERTYPENAME>Payment</VOUCHERTYPENAME>
                          <VOUCHERNUMBER>{ref_no}</VOUCHERNUMBER>
                          <NARRATION>Being inv no {inv_no} drawn on {notify_party} now refunded to bank.</NARRATION>
                        """

             # Dr Bank bank iability (DPDA)
            bill_details=[{"name": inv_no, "type": "New Ref", "amount": ref_amt}]
            voucher += self.ledger_entry(bank_dpda, ref_amt, is_party=True, bill_details=bill_details)

             # Dr Bank Charge:
            if bank_charge != 0:
                voucher += self.ledger_entry(ledger="Bank Charges - EB",amount=bank_charge)
                
            # Dr Interest:    
            if interest != 0:
                voucher += self.ledger_entry(ledger="Interest Paid - (EB-DP-DA)",amount=interest)
                
            # Cr bank_amount:
            voucher += self.ledger_entry(ledger= bank_name,amount= bank_amount,is_party=True)
        
            voucher += """
                     </VOUCHER>
                    </TALLYMESSAGE>
                    """
            vouchers_xml.append(voucher)
    
    
        # -----------------------------
        # Write Final XML
        # -----------------------------
        final_xml = f"""<ENVELOPE>
                 <HEADER>
                  <TALLYREQUEST>Import Data</TALLYREQUEST>
                 </HEADER>
                 <BODY>
                  <IMPORTDATA>
                   <REQUESTDESC>
                    <REPORTNAME>Vouchers</REPORTNAME>
                    <STATICVARIABLES>
                     <SVCURRENTCOMPANY>{self.company}</SVCURRENTCOMPANY>
                    </STATICVARIABLES>
                   </REQUESTDESC>
                   <REQUESTDATA>
                {''.join(vouchers_xml)}
                   </REQUESTDATA>
                  </IMPORTDATA>
                 </BODY>
                </ENVELOPE>
                """
        return final_xml
    
    # ---------- Function for Generate Doc Received XML---------- (This is final)
    def generate_doc_rec_xml(self, df: pd.DataFrame) -> None:
        vouchers_xml = []
    
        for i, r in df.iterrows():
            inv_no = self.escape_xml(r["inv_no"])
            ref_no = self.escape_xml(r["ref_no"])
            bank_name = self.escape_xml(r["bank_name"])
            bank_dpda = self.escape_xml(r["bank_dpda"])
            customer = self.escape_xml(r["customer_doc"])
            notify_party = self.escape_xml(r["notify_party"])

            # Date -----------------------------
            date = self.fmt_date(r["date"])
    
            # -----------------------------
            # Amounts
            # -----------------------------
            bank_liability = self.clean_amount(r["bank_liability"])
            rec_amount     = self.clean_amount(r["rec_amount"])
            bank_amount    = self.clean_amount(r["bank_amount"])
            interest       = self.clean_amount(r.get("interest", 0))
            bank_charge    = self.clean_amount(r.get("bank_charge", 0))

             # 🔒 Financial validation
            amount_tally = round(bank_liability + rec_amount + bank_amount + interest + bank_charge, 2)
            if round(amount_tally, 2) != 0:
                raise ValueError(
                    f"❌ Amount mismatch at row {i+1} (Invoice {inv_no})"
                )
    
            # -----------------------------
            # Determine Voucher Type
            # -----------------------------
            if bank_amount > 0:
                vch_type = "Receipt"
            elif bank_amount < 0:
                vch_type = "Payment"
            else:
                vch_type = "Journal"
    
            # -----------------------------
            # Build Voucher XML
            # -----------------------------
            voucher = f"""
                        <TALLYMESSAGE>
                         <VOUCHER ACTION="Create" VCHTYPE="{vch_type}">
                          <DATE>{date}</DATE>
                          <VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME>
                          <VOUCHERNUMBER>{ref_no}</VOUCHERNUMBER>
                          <NARRATION>Being payment made by {notify_party} against inv no {inv_no}</NARRATION>
                        """
            if vch_type == "Receipt": # Beause of in Tally in Received mode always 1st credit entry
                if rec_amount != 0:
                    if customer == "UXL- China (CC)":
                        voucher += self.ledger_entry(customer, rec_amount, is_party=True)
                    else:
                        bill_details=[{"name": inv_no, "type": "Agst Ref", "amount": rec_amount}]
                        voucher += self.ledger_entry(customer, rec_amount, is_party=True, bill_details=bill_details)
                     
                if bank_liability != 0:
                    bill_details=[{"name": inv_no, "type": "Agst Ref", "amount": abs(bank_liability)}]
                    voucher += self.ledger_entry(ledger=bank_dpda, amount=bank_liability, bill_details=bill_details)
    
                if interest != 0:
                    voucher += self.ledger_entry(ledger="Interest Paid - (EB-DP-DA)",amount=interest)
    
                if bank_charge != 0:
                    voucher += self.ledger_entry(ledger="Bank Charges - EB", amount=bank_charge )
        
                if bank_amount != 0:
                    voucher += self.ledger_entry(ledger=bank_name,amount=bank_amount,is_party=True)
                
            else:
                if bank_liability != 0:
                    bill_details=[{"name": inv_no, "type": "Agst Ref", "amount": abs(bank_liability)}]
                    voucher += self.ledger_entry(ledger=bank_dpda, amount=bank_liability, bill_details=bill_details)
    
                if interest != 0:
                    voucher += self.ledger_entry(ledger="Interest Paid - (EB-DP-DA)",amount=interest)
    
                if bank_charge != 0:
                    voucher += self.ledger_entry(ledger="Bank Charges - EB", amount=bank_charge )
                if rec_amount != 0:
                    if customer == "UXL- China (CC)":
                        voucher += self.ledger_entry(customer, rec_amount, is_party=True)
                    else:
                        bill_details=[{"name": inv_no, "type": "Agst Ref", "amount": rec_amount}]
                        voucher += self.ledger_entry(ledger=customer, amount=rec_amount, is_party=True, bill_details=bill_details)
        
                if bank_amount != 0:
                    voucher += self.ledger_entry(ledger=bank_name,amount=bank_amount,is_party=True)
        
        
            voucher += """
                     </VOUCHER>
                    </TALLYMESSAGE>
                    """
            vouchers_xml.append(voucher)
        # -----------------------------
        # Write Final XML
        # -----------------------------
        final_xml = f"""<ENVELOPE>
                 <HEADER>
                  <TALLYREQUEST>Import Data</TALLYREQUEST>
                 </HEADER>
                 <BODY>
                  <IMPORTDATA>
                   <REQUESTDESC>
                    <REPORTNAME>Vouchers</REPORTNAME>
                    <STATICVARIABLES>
                     <SVCURRENTCOMPANY>{self.company}</SVCURRENTCOMPANY>
                    </STATICVARIABLES>
                   </REQUESTDESC>
                   <REQUESTDATA>
                {''.join(vouchers_xml)}
                   </REQUESTDATA>
                  </IMPORTDATA>
                 </BODY>
                </ENVELOPE>
                """
        return final_xml

        # ---------- Function for Generate Doc Received XML---------- (This is final)
    def generate_interest_paid_xml(self, df: pd.DataFrame) -> None:
        vouchers_xml = []
    
        for i, r in df.iterrows():
            inv_no = self.escape_xml(r["inv_no"])
            ref_no = self.escape_xml(r["ref_no"])
            bank_name = self.escape_xml(r["bank_name"])

            # Date -----------------------------
            date = self.fmt_date(r["date"])
    
            # Amounts -----------------------------
            bank_amount    = self.clean_amount(r["bank_amount"])
            interest       = self.clean_amount(r.get("interest", 0))

            # 🔒 Financial validation
            amount_tally = round(bank_amount + interest, 2)
            if round(amount_tally, 2) != 0:
                raise ValueError(
                    f"❌ Amount mismatch at row {i+1} (Invoice {inv_no})"
                )
    
            # -----------------------------
            # Build Voucher XML
            # -----------------------------
            voucher = f"""
                        <TALLYMESSAGE>
                         <VOUCHER ACTION="Create" VCHTYPE="Payment">
                          <DATE>{date}</DATE>
                          <VOUCHERTYPENAME>Payment</VOUCHERTYPENAME>
                          <VOUCHERNUMBER>{ref_no}</VOUCHERNUMBER>
                          <NARRATION>Being interest paid for inv no {inv_no}</NARRATION>
                        """
            if interest != 0:
                    voucher += self.ledger_entry(ledger="Interest Paid - (EB-DP-DA)",amount=interest)
                
            if bank_amount != 0:
                    voucher += self.ledger_entry(ledger=bank_name,amount=bank_amount,is_party=True)
        
            voucher += """
                     </VOUCHER>
                    </TALLYMESSAGE>
                    """
            vouchers_xml.append(voucher)

        # -----------------------------
        # Write Final XML
        # -----------------------------
        final_xml = f"""<ENVELOPE>
                 <HEADER>
                  <TALLYREQUEST>Import Data</TALLYREQUEST>
                 </HEADER>
                 <BODY>
                  <IMPORTDATA>
                   <REQUESTDESC>
                    <REPORTNAME>Vouchers</REPORTNAME>
                    <STATICVARIABLES>
                     <SVCURRENTCOMPANY>{self.company}</SVCURRENTCOMPANY>
                    </STATICVARIABLES>
                   </REQUESTDESC>
                   <REQUESTDATA>
                {''.join(vouchers_xml)}
                   </REQUESTDATA>
                  </IMPORTDATA>
                 </BODY>
                </ENVELOPE>
                """
        return final_xml


         # ---------- Function for Generate Doc Received XML---------- 
    def generate_cc_received_xml(self, df: pd.DataFrame) -> None:
        vouchers_xml = []
    
        for i, r in df.iterrows():
            customer_cc = self.escape_xml(r["customer_cc"])
            customer = self.escape_xml(r["customer"])
            ref_no = self.escape_xml(r["ref_no"])
            bank_name = self.escape_xml(r["bank_name"])
            date = self.fmt_date(r["date"])
    
            # -----------------------------
            # Amounts
            # -----------------------------
            cc_received    = self.clean_amount(r["cc_received"])
            bank_charge       = self.clean_amount(r["bank_charge"])
            bank_amount    = self.clean_amount(r["bank_amount"])

             # 🔒 Financial validation
            amount_tally = round(cc_received + bank_charge + bank_amount, 2)
            if round(amount_tally, 2) != 0:
                raise ValueError(
                    f"❌ Amount mismatch at row {i+1} (Ref No {ref_no})"
                )
    
            # -----------------------------
            # Build Voucher XML
            # -----------------------------
            voucher = f"""
                        <TALLYMESSAGE>
                         <VOUCHER ACTION="Create" VCHTYPE="Receipt">
                          <DATE>{date}</DATE>
                          <VOUCHERTYPENAME>Receipt</VOUCHERTYPENAME>
                          <VOUCHERNUMBER>{ref_no}</VOUCHERNUMBER>
                          <NARRATION>Being USD {abs(cc_received):,.2f} received from {customer}</NARRATION>
                        """
            if cc_received != 0:
                    voucher += self.ledger_entry(ledger=customer_cc,amount=cc_received, is_party=True)
                
            if bank_charge != 0:
                    voucher += self.ledger_entry(ledger="Bank Charges (TTs, DDs &amp; Others)",amount=bank_charge)
                
            if bank_amount != 0:
                    voucher += self.ledger_entry(ledger=bank_name,amount=bank_amount,is_party=True)
        
            voucher += """
                     </VOUCHER>
                    </TALLYMESSAGE>
                    """
            vouchers_xml.append(voucher)
    
    
        # -----------------------------
        # Write Final XML
        # -----------------------------
        final_xml = f"""<ENVELOPE>
                 <HEADER>
                  <TALLYREQUEST>Import Data</TALLYREQUEST>
                 </HEADER>
                 <BODY>
                  <IMPORTDATA>
                   <REQUESTDESC>
                    <REPORTNAME>Vouchers</REPORTNAME>
                    <STATICVARIABLES>
                     <SVCURRENTCOMPANY>{self.company}</SVCURRENTCOMPANY>
                    </STATICVARIABLES>
                   </REQUESTDESC>
                   <REQUESTDATA>
                {''.join(vouchers_xml)}
                   </REQUESTDATA>
                  </IMPORTDATA>
                 </BODY>
                </ENVELOPE>
                """
        return final_xml

    # ---------- Function for Generating Cost Center Creation XML ---------- 
    def generate_create_cost_center_xml(self, cost_centers: list) -> str:
        masters_xml = []
    
        for cc in cost_centers:
            # String parsing & escaping directly from the list elements
            cc_name = self.escape_xml(cc)
            
            # Skip empty entries gracefully
            if not cc_name:
                continue
                
            # Flush string literals completely to the left margin to eliminate trailing blank lines
            master = f"""<TALLYMESSAGE xmlns:UDF="TallyUDF">
                <COSTCENTER NAME="{cc_name}" ACTION="Create">
                <NAME.LIST>
                <NAME>{cc_name}</NAME>
                </NAME.LIST>
                <CATEGORY>Primary Cost Category</CATEGORY>
                <PARENT/>
                <REVENUELEAF>Yes</REVENUELEAF>
                <FORREVENUE>Yes</FORREVENUE>
                </COSTCENTER>
                </TALLYMESSAGE>"""
            masters_xml.append(master)
    
        # Join nodes seamlessly with a clean single newline character
        masters_joined = "\n".join(masters_xml)
        
        # Assemble root wrapper envelope flat against the edge
        final_xml = f"""<ENVELOPE>
            <HEADER>
            <TALLYREQUEST>Import Data</TALLYREQUEST>
            </HEADER>
            <BODY>
            <IMPORTDATA>
            <REQUESTDESC>
            <REPORTNAME>All Masters</REPORTNAME>
            <STATICVARIABLES>
            <SVCURRENTCOMPANY>{self.company}</SVCURRENTCOMPANY>
            </STATICVARIABLES>
            </REQUESTDESC>
            <REQUESTDATA>
            {masters_joined}
            </REQUESTDATA>
            </IMPORTDATA>
            </BODY>
            </ENVELOPE>"""
        
        return final_xml