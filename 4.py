import streamlit as st
from fpdf import FPDF
import datetime
import os

# --- PAGE SETUP ---
st.set_page_config(page_title="Tax Client Intake 2025/2026", layout="wide")
st.title("Tax Client Intake Form – 2025/2026")

# --- DATA SAFETY HELPER ---
def clean_text(text):
    """Ensures text is safe for the PDF engine."""
    if text is None or text == "" or text == "None":
        return "-"
    return str(text).replace("•", "-").replace("—", "-").replace("–", "-").replace("’", "'").replace("“", '"').replace("”", '"')

# --- SECURITY WARNING ---
st.warning("⚠️ **SECURITY NOTICE:** Do not include Social Security Numbers or sensitive banking details in this form. Use our secure portal for document uploads.")

# --- 1. PERSONAL INFORMATION ---
with st.container(border=True):
    st.header("1. Personal Information")
    col1, col2 = st.columns(2)
    with col1:
        tp_name = st.text_input("Taxpayer Full Name")
        tp_dob = st.date_input("Taxpayer Date of Birth", value=None)
    with col2:
        sp_name = st.text_input("Spouse Full Name (if applicable)")
        sp_dob = st.date_input("Spouse Date of Birth", value=None)
    
    address = st.text_area("Mailing Address", placeholder="Street, City, State, Zip")
    
    col3, col4 = st.columns(2)
    with col3: phone = st.text_input("Phone Number")
    with col4: email = st.text_input("Email Address")
    
    status = st.selectbox("Filing Status", ["Single", "Married Filing Jointly", "Married Filing Separately", "Head of Household", "Unsure"])

# --- 2. DEPENDENTS ---
st.header("2. Dependents")
num_deps = st.number_input("How many dependents are you claiming?", 0, 15, 0)

dep_list = []
for i in range(num_deps):
    with st.container(border=True):
        st.subheader(f"Dependent #{i+1}")
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1: d_name = st.text_input("Full Name", key=f"dname_{i}")
        with c2: d_rel = st.selectbox("Relationship", ["Child", "Parent", "Step-child", "Other"], key=f"drel_{i}")
        with c3: d_dob = st.date_input("Date of Birth", value=None, key=f"ddob_{i}")
        
        dep_list.append({
            "name": d_name, 
            "rel": d_rel, 
            "dob": str(d_dob) if d_dob else "N/A"
        })

# --- 3. INCOME & 4. DEDUCTIONS ---
with st.form("financial_info_form"):
    st.header("3. Income")
    incomes = st.multiselect("Select all applicable income sources:", 
                             ["W-2 Wages", "Interest/Dividends", "K-1 Income (Partnerships/S-Corps)", 
                              "Capital Gains (Stocks/Crypto)", "Gambling Winnings (W-2G or Casual)", 
                              "Retirement/IRA Distributions", "Social Security", "Self-Employment", 
                              "Rental Income", "Unemployment"])

    st.subheader("Personal Item Sales (eBay, Garage Sales, etc.)")
    personal_sales = st.radio(
        "Did you sell personal items (clothes, furniture, electronics) this year?",
        ["No", "Yes - I sold them for LESS than I originally paid (Non-taxable loss)", 
         "Yes - I sold them for MORE than I paid (Taxable gain)", "Unsure"]
    )

    st.header("4. Deductions & Credits")
    deductions = st.multiselect("Select all applicable deductions/credits:", 
                                ["IRA Contribution", "Student Loan Interest", "Mortgage Interest", 
                                 "Charitable Giving", "Child Tax Credit", "Energy Credits", 
                                 "HSA Contribution", "Gambling Losses (only deductible up to amount of winnings)"])

    st.subheader("Medical & Dental Expenses")
    st.info("💡 Note: You can usually only deduct medical expenses that exceed 7.5% of your Adjusted Gross Income (AGI).")
    medical_check = st.checkbox("I had significant out-of-pocket medical/dental expenses this year.")
    medical_notes = st.text_input("Brief description of major medical costs (e.g., Surgery, Orthodontics, etc.)", 
                                  disabled=not medical_check)

    st.header("5. Additional Notes")
    notes = st.text_area("Any other life changes, questions, or notes for your preparer?")
    
    submitted = st.form_submit_button("Generate Summary PDF", type="primary")

# --- PDF ENGINE ---
class TaxPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(40, 40, 40)
        self.cell(0, 10, "CLIENT INTAKE SUMMARY", ln=True, align="L")
        
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, f"Tax Year: 2025/2026 | Generated: {datetime.date.today()}", ln=True, align="L")
        self.ln(10)

    def add_section_header(self, title):
        self.set_fill_color(240, 240, 240)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, f" {title}", ln=True, fill=True)
        self.ln(3)

    def add_field(self, label, value):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, clean_text(label).upper(), ln=True)
        
        self.set_font("Helvetica", "", 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, clean_text(value))
        self.ln(3)

if submitted:
    if not tp_name:
        st.error("⚠️ Please enter the Taxpayer Name.")
    else:
        pdf = TaxPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Section 1
        pdf.add_section_header("1. PERSONAL INFORMATION")
        pdf.add_field("Taxpayer Name", tp_name)
        pdf.add_field("Taxpayer DOB", str(tp_dob))
        pdf.add_field("Spouse Name", sp_name)
        pdf.add_field("Spouse DOB", str(sp_dob))
        pdf.add_field("Address", address.replace("\n", ", "))
        pdf.add_field("Contact", f"Ph: {phone} / Email: {email}")
        pdf.add_field("Filing Status", status)

        # Section 2
        pdf.ln(2)
        pdf.add_section_header("2. DEPENDENTS")
        if num_deps > 0:
            for d in dep_list:
                info = f"{d['name']} ({d['rel']}) | DOB: {d['dob']}"
                pdf.multi_cell(0, 7, f"- {clean_text(info)}")
                pdf.ln(1)
        else:
            pdf.cell(0, 8, "No dependents listed.", ln=True)

        # Section 3
        pdf.ln(5)
        pdf.add_section_header("3. INCOME")
        pdf.add_field("General Income Sources", ", ".join(incomes) if incomes else "None selected")
        pdf.add_field("Personal Property Sales", personal_sales)

        # Section 4
        pdf.ln(5)
        pdf.add_section_header("4. DEDUCTIONS & CREDITS")
        pdf.add_field("Deductions Selected", ", ".join(deductions) if deductions else "None selected")
        if medical_check:
            pdf.add_field("Significant Medical Expenses", medical_notes if medical_notes else "Yes (details to follow)")
        
        # Section 5
        pdf.ln(5)
        pdf.add_section_header("5. ADDITIONAL NOTES")
        pdf.multi_cell(0, 7, clean_text(notes) if notes else "No additional notes.")

        try:
            pdf_output = bytes(pdf.output())
            st.download_button(
                label="📥 DOWNLOAD PDF SUMMARY",
                data=pdf_output,
                file_name=f"Tax_Intake_{tp_name.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
            st.success("✅ PDF is ready for download!")
        except Exception as e:
            st.error(f"❌ Error: {e}")