import streamlit as st
import pandas as pd
import pdfplumber
import re
from rapidfuzz import process, fuzz

# ---------------- LOGIN ---------------- #

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

# ---------------- APP START ---------------- #

st.set_page_config(page_title="AffiNexa AI Operations", layout="wide")
st.title("AffiNexa AI Operations Control Panel")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Upload Excel",
    "Product Grouping",
    "Upload PDF",
    "Dashboard",
    "Department Tasks",
    "Courier Tracker"
])

if "df" not in st.session_state:
    st.session_state.df = None

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# ---------------- TAB 1 : EXCEL ---------------- #

with tab1:

    st.header("Upload Product Excel")

    excel = st.file_uploader("Upload Excel file", type=["xlsx"])

    if excel:
        df = pd.read_excel(excel)
        st.session_state.df = df
        st.dataframe(df)

# ---------------- TAB 2 : PRODUCT GROUPING ---------------- #

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
                df["item order"].astype(str)
                + " | "
                + df["item size"].astype(str)
                + " | "
                + df["item color"].astype(str)
            )

            product_list = df["product_key"].unique()

            grouped = {}
            used = set()

            for prod in product_list:

                if prod in used:
                    continue

                matches = process.extract(
                    prod,
                    product_list,
                    scorer=fuzz.ratio,
                    limit=10
                )

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

# ---------------- TAB 3 : PDF READER ---------------- #

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

        st.text_area("PDF Text", extracted, height=250)

        lines = extracted.split("\n")
        buyer = lines[0] if lines else "Not detected"

        qty_matches = re.findall(
            r"(?:qty|quantity|pcs|pieces)\s*[:\-]?\s*(\d+)",
            extracted.lower()
        )

        if not qty_matches:
            all_numbers = re.findall(r"\b\d+\b", extracted)
            qty_matches = [n for n in all_numbers if 0 < int(n) < 10000]

        st.subheader("Detected Invoice Info")

        col1, col2 = st.columns(2)

        with col1:
            st.success(f"Buyer: {buyer}")

        with col2:
            if qty_matches:
                st.success(f"Quantity: {qty_matches[0]}")
            else:
                st.warning("Quantity not detected")

        st.markdown("---")

        st.subheader("Procurement Alert")

        supplier = st.text_input("Supplier Email")

        deadline = st.date_input("Procurement Deadline")

        if st.button("Send Procurement Alert"):
            st.success("Alert sent to supplier and internal team")
            st.info(f"Deadline: {deadline}")
            st.info("Reminders scheduled (T-3, T-1, Due Day)")

# ---------------- TAB 4 : DASHBOARD ---------------- #

with tab4:

    st.header("Operations Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    if st.session_state.df is not None:
        total_records = len(st.session_state.df)
    else:
        total_records = 0

    with col1:
        st.metric("Total Records", total_records)

    with col2:
        st.metric("Active Tasks", "3")

    with col3:
        st.metric("Active Shipments", "2")

    with col4:
        if st.session_state.pdf_text:
            st.metric("Invoice Loaded", "Yes")
        else:
            st.metric("Invoice Loaded", "No")

    st.markdown("---")

    st.subheader("System Overview")

    st.write("• Order uploads")
    st.write("• Department coordination")
    st.write("• Procurement alerts")
    st.write("• Courier tracking")

# ---------------- TAB 5 : DEPARTMENT TASKS ---------------- #

with tab5:

    st.header("Department Communication")

    task = st.text_input("Task Description")

    department = st.selectbox(
        "Department",
        ["Procurement", "Raw Material", "Polishing", "Packaging", "Dispatch"]
    )

    deadline = st.date_input("Task Deadline")

    if st.button("Create Task"):
        st.success(f"Task assigned to {department}")

    st.subheader("Update Task Status")

    status = st.selectbox(
        "Status",
        ["Pending", "In Progress", "Completed"]
    )

    if st.button("Update Status"):
        st.success(f"Task status updated to {status}")

# ---------------- TAB 6 : COURIER TRACKER ---------------- #

with tab6:

    st.header("Courier / AWB Tracking")

    courier = st.selectbox(
        "Courier Company",
        ["Blue Dart", "DTDC", "Delhivery", "DHL", "FedEx"]
    )

    awb = st.text_input("AWB Number")

    destination = st.text_input("Destination")

    if st.button("Track Shipment"):
        st.success("Tracking information fetched")
        st.write("Status: In Transit")
        st.write("Expected Delivery: 3 Days")