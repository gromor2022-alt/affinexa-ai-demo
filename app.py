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
                st.experimental_rerun()
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

        # Simple buyer + qty extraction
        buyer = extracted.split("\n")[0]

        qty = re.findall(r"\b\d+\b", extracted)

        st.success(f"Buyer (approx): {buyer}")
        if qty:
            st.success(f"Quantities found: {qty[:5]}")

# ---------------- TAB 4 ----------------

with tab4:
    st.header("Mini Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        if st.session_state.df is not None:
            st.metric("Total Rows", len(st.session_state.df))
        else:
            st.metric("Total Rows", 0)

    with col2:
        if st.session_state.pdf_text:
            st.metric("PDF Loaded", "Yes")
        else:
            st.metric("PDF Loaded", "No")
