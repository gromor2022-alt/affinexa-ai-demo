import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
import pdfplumber
import re

# ---------------- LOGIN ----------------

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("AffiNexa AI Demo Login")

        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")

        if st.button("Login"):
            if user == "demo" and pwd == "AffiNexa@123":
                st.session_state.logged_in = True
                st.rerun()

            else:
                st.error("Invalid credentials")

        st.stop()

check_login()

# ---------------- APP START ----------------

st.set_page_config(page_title="AffiNexa AI Demo", layout="wide")
st.title("AffiNexa AI Operations Demo")

tab1, tab2, tab3, tab4 = st.tabs(["Upload Excel", "Product Grouping", "Upload PDF", "Dashboard"])

if "df" not in st.session_state:
    st.session_state.df = None

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# ---------------- TAB 1 ----------------

with tab1:
    st.header("Upload Product Excel")

    excel = st.file_uploader("Upload Excel file", type=["xlsx"])

    if excel:
        df = pd.read_excel(excel)
        st.session_state.df = df
        st.dataframe(df)

# ---------------- TAB 2 ----------------

with tab2:
    st.header("Product Grouping")

    if st.session_state.df is not None:
        df = st.session_state.df.copy()
        df.columns = df.columns.str.lower().str.strip()

        if "item order" in df.columns and "item size" in df.columns:

            if "item color" not in df.columns:
                df["item color"] = ""

            df["item color"] = df["item color"].fillna("")

            df["product_key"] = (
                df["item order"].astype(str) + " | " +
                df["item size"].astype(str) + " | " +
                df["item color"].astype(str)
            )

            product_list = df["product_key"].unique()

            grouped = {}
            used = set()

            for prod in product_list:
                if prod in used:
                    continue

                matches = process.extract(prod, product_list, scorer=fuzz.ratio, limit=10)
                similar = [m[0] for m in matches if m[1] > 80]

                grouped[prod] = similar
                for s in similar:
                    used.add(s)

            for master, variants in grouped.items():
                st.subheader(master)
                st.write(f"Variants: {len(variants)}")
                st.write(variants)

        else:
            st.warning("Required columns not found")

# ---------------- TAB 3 ----------------

with tab3:
    st.header("Upload Invoice PDF")

    pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if pdf:
        extracted = ""

        with pdfplumber.open(pdf) as pdf_file:
            for page in pdf_file.pages:
                t = page.extract_text()
                if t:
                    extracted += t + "\n"

        st.session_state.pdf_text = extracted

        st.text_area("PDF Text", extracted, height=300)

        lines = extracted.split("\n")
        buyer = lines[0] if lines else "Not detected"

        qty_matches = re.findall(r"\b\d+(?:\.\d+)?\b", extracted)

        st.subheader("Detected Invoice Info")

        col1, col2 = st.columns(2)

        with col1:
            st.success(f"Buyer (approx): {buyer}")

        with col2:
            if qty_matches:
                st.success(f"Quantities detected: {', '.join(qty_matches[:5])}")
            else:
                st.warning("Quantity not detected")

        st.markdown("---")
        st.subheader("Procurement Alert (Demo)")

        supplier_email = st.text_input("Supplier / Procurement Email")
        deadline = st.date_input("Procurement Deadline")

        if st.button("Send Procurement Alert"):
            st.success("Procurement alert sent to supplier and internal team.")
            st.info(f"Deadline set: {deadline}")
            st.info("Automatic reminders scheduled for T-3 days, T-1 day, and Due Date.")



# ---------------- TAB 4 ----------------

with tab4:
    st.header("Operations Dashboard")

    col1, col2, col3 = st.columns(3)

    # Total Rows
    if st.session_state.df is not None:
        total_rows = len(st.session_state.df)
        unique_products = st.session_state.df["item order"].nunique() if "item order" in st.session_state.df.columns else 0
    else:
        total_rows = 0
        unique_products = 0

    with col1:
        st.metric("Total Records", total_rows)

    with col2:
        st.metric("Unique Product Orders", unique_products)

    with col3:
        status = "Loaded" if st.session_state.pdf_text else "Not Loaded"
        st.metric("Invoice Status", status)
