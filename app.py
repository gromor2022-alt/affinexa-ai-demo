import streamlit as st
import pandas as pd
import pdfplumber
import re
from rapidfuzz import process, fuzz

st.set_page_config(page_title="AffiNexa Operations", layout="wide")

# ---------------- UI STYLE ---------------- #

st.markdown("""
<style>
.main {background-color:#f5f7fb;}
h1 {color:#1f4e79;}
.stMetric {background-color:white;padding:15px;border-radius:10px;border:1px solid #e6e6e6;}
</style>
""", unsafe_allow_html=True)

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

# ---------------- SESSION STORAGE ---------------- #

if "df" not in st.session_state:
    st.session_state.df = None

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# ---------------- HEADER ---------------- #

st.title("Banares Beads Operations Control System")

st.markdown(
"Central dashboard for *order intake, department coordination and shipment tracking*"
)

# ---------------- TABS ---------------- #

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Dashboard",
    "Upload Excel",
    "Product Grouping",
    "Upload Sales Contract",
    "Department Tasks",
    "Courier Tracker"
])

# ---------------- DASHBOARD ---------------- #

with tab1:

    st.header("Operations Dashboard")

    total_records = len(st.session_state.df) if st.session_state.df is not None else 0
    active_tasks = len(st.session_state.tasks)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Orders Loaded", total_records)
    col2.metric("Department Tasks", active_tasks)
    col3.metric("Active Shipments", 2)
    col4.metric("Departments Active", 5)

    st.markdown("---")

    st.subheader("Department Task Overview")

    if st.session_state.tasks:
        st.dataframe(pd.DataFrame(st.session_state.tasks))
    else:
        st.info("No tasks created yet")

# ---------------- EXCEL UPLOAD ---------------- #

with tab2:

    st.header("Upload Sales / Order Excel")

    excel = st.file_uploader("Upload Excel file", type=["xlsx"])

    if excel:

        df = pd.read_excel(excel)
        st.session_state.df = df

        st.success("Excel uploaded successfully")
        st.dataframe(df)

        if st.button("Generate Department Tasks"):

            departments = [
                "Procurement",
                "Raw Material",
                "Polishing",
                "Packaging",
                "Dispatch"
            ]

            for dept in departments:

                st.session_state.tasks.append({
                    "Department": dept,
                    "Task": "Process Sales Contract",
                    "Status": "Pending"
                })

            st.success("Tasks automatically generated from Sales Contract")

# ---------------- PRODUCT GROUPING ---------------- #

with tab3:

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
                st.write("Variants:", variants)

        else:
            st.warning("Required columns not found")

# ---------------- PDF READER ---------------- #

with tab4:

    st.header("Upload Sales Contract / Invoice")

    pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if pdf:

        extracted = ""

        with pdfplumber.open(pdf) as pdf_file:

            for page in pdf_file.pages:

                t = page.extract_text()

                if t:
                    extracted += t + "\n"

        st.session_state.pdf_text = extracted

        st.text_area("Extracted Text", extracted, height=250)

        lines = extracted.split("\n")
        buyer = lines[0] if lines else "Not detected"

        qty_matches = re.findall(
            r"(?:qty|quantity|pcs|pieces)\s*[:\-]?\s*(\d+)",
            extracted.lower()
        )

        if not qty_matches:
            numbers = re.findall(r"\b\d+\b", extracted)
            qty_matches = [n for n in numbers if 0 < int(n) < 10000]

        col1, col2 = st.columns(2)

        col1.success(f"Buyer: {buyer}")

        if qty_matches:
            col2.success(f"Quantity: {qty_matches[0]}")
        else:
            col2.warning("Quantity not detected")

# ---------------- DEPARTMENT TASKS ---------------- #

with tab5:

    st.header("Department Task Board")

    if st.session_state.tasks:

        pending = []
        progress = []
        completed = []

        for task in st.session_state.tasks:

            if task["Status"] == "Pending":
                pending.append(task)

            elif task["Status"] == "In Progress":
                progress.append(task)

            else:
                completed.append(task)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("Pending")

            for t in pending:

                st.markdown(f"""
                *Department:* {t['Department']}  
                *Task:* {t['Task']}
                """)

        with col2:
            st.subheader("In Progress")

            for t in progress:

                st.markdown(f"""
                *Department:* {t['Department']}  
                *Task:* {t['Task']}
                """)

        with col3:
            st.subheader("Completed")

            for t in completed:

                st.markdown(f"""
                *Department:* {t['Department']}  
                *Task:* {t['Task']}
                """)

        st.markdown("---")

        st.subheader("Update Task Status")

        for i, task in enumerate(st.session_state.tasks):

            col1, col2, col3 = st.columns(3)

            col1.write(task["Department"])
            col2.write(task["Task"])

            status = col3.selectbox(
                "Status",
                ["Pending", "In Progress", "Completed"],
                index=["Pending","In Progress","Completed"].index(task["Status"]),
                key=f"status_{i}"
            )

            st.session_state.tasks[i]["Status"] = status

    else:
        st.info("No tasks created yet. Upload Excel to generate tasks.")

# ---------------- COURIER TRACKER ---------------- #

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