import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
import pdfplumber

st.set_page_config(page_title="AffiNexa AI Demo", layout="wide")

st.title("AffiNexa AI Operations Demo")

tab1, tab2, tab3 = st.tabs(["Upload Excel", "Product Grouping", "Upload PDF"])

if "df" not in st.session_state:
    st.session_state.df = None

# ---------------- TAB 1 ----------------

with tab1:
    st.header("Upload Product Excel")

    excel = st.file_uploader("Upload Excel file", type=["xlsx"])

    if excel:
        df = pd.read_excel(excel)
        st.session_state.df = df

        st.subheader("Raw Uploaded Data")
        st.dataframe(df)

# ---------------- TAB 2 ----------------

with tab2:
    st.header("Product Grouping (Order + Size + Color)")

    if st.session_state.df is not None:
        df = st.session_state.df.copy()

        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()

        if "item order" in df.columns and "item size" in df.columns:

            # Handle missing color
            if "item color" not in df.columns:
                df["item color"] = ""

            df["item color"] = df["item color"].fillna("")

            # Create product key
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
                st.subheader(f"Master Product: {master}")
                st.write(f"Total Variants: {len(variants)}")
                st.write(variants)

        else:
            st.warning("Required columns not found: item order / item size")

    else:
        st.info("Upload Excel first.")

# ---------------- TAB 3 ----------------

with tab3:
    st.header("Upload Invoice PDF")

    pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if pdf:
        extracted_text = ""

        with pdfplumber.open(pdf) as pdf_file:
            for page in pdf_file.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"

        st.subheader("Extracted Text From PDF")
        st.text_area("PDF Content", extracted_text, height=400)