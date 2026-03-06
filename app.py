import streamlit as st
import pandas as pd
import pdfplumber
import re
from rapidfuzz import process, fuzz

st.set_page_config(page_title="Banares Beads Operations", layout="wide")

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

if "alerts" not in st.session_state:
    st.session_state.alerts = []

# ---------------- HEADER ---------------- #

st.title("Banares Beads Operations Control System")

st.markdown(
"Central dashboard for *order processing, department coordination and shipment tracking*"
)

# ---------------- TABS ---------------- #

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Dashboard",
    "Upload Sales Contract",
    "Product Grouping",
    "Upload PDF",
    "Department Tasks",
    "Courier Tracking"
])

# ---------------- DASHBOARD ---------------- #

with tab1:

    st.header("Operations Dashboard")

    orders = len(st.session_state.df) if st.session_state.df is not None else 0
    tasks = len(st.session_state.tasks)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Orders Loaded", orders)
    col2.metric("Department Tasks", tasks)
    col3.metric("Active Shipments", 2)
    col4.metric("Departments Active", 5)

    st.markdown("---")

    st.subheader("Order Progress Tracker")

    if st.session_state.tasks:

        df = pd.DataFrame(st.session_state.tasks)

        summary = df.groupby("Department")["Status"].value_counts().unstack().fillna(0)

        st.dataframe(summary)

    else:

        st.info("No tasks created yet")

    st.markdown("---")

    st.subheader("Recent Activity Alerts")

    if st.session_state.alerts:

        for alert in st.session_state.alerts[-5:]:

            st.info(alert)

    else:

        st.write("No alerts yet")

# ---------------- UPLOAD EXCEL ---------------- #

with tab2:

    st.header("Upload Sales Contract Excel")

    excel = st.file_uploader("Upload Excel", type=["xlsx"])

    if excel:

        df = pd.read_excel(excel)

        st.session_state.df = df

        st.success("Sales contract uploaded")

        st.dataframe(df)

        if st.button("Generate Smart Tasks"):

            df.columns = df.columns.str.lower().str.strip()

            if "item order" in df.columns:

                unique_products = df["item order"].unique()

                for product in unique_products:

                    departments = [
                        ("Procurement", f"Procure raw material for {product}"),
                        ("Polishing", f"Polish batch for {product}"),
                        ("Packaging", f"Pack finished goods for {product}"),
                        ("Dispatch", f"Prepare dispatch for {product}")
                    ]

                    for dept, desc in departments:

                        st.session_state.tasks.append({
                            "Department": dept,
                            "Task": desc,
                            "Status": "Pending"
                        })

                st.success("Smart tasks generated automatically")

            else:

                st.warning("Column 'item order' not found")

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

            for product in product_list:

                st.subheader(product)

        else:

            st.warning("Required columns missing")

# ---------------- PDF READER ---------------- #

with tab4:

    st.header("Upload Sales Contract / Invoice")

    pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if pdf:

        extracted = ""

        with pdfplumber.open(pdf) as pdf_file:

            for page in pdf_file.pages:

                text = page.extract_text()

                if text:
                    extracted += text + "\n"

        st.text_area("Extracted Text", extracted, height=250)

        lines = extracted.split("\n")

        buyer = lines[0] if lines else "Not detected"

        qty = re.findall(r"\b\d+\b", extracted)

        col1, col2 = st.columns(2)

        col1.success(f"Buyer: {buyer}")

        if qty:
            col2.success(f"Quantity Detected: {qty[0]}")
        else:
            col2.warning("Quantity not detected")

# ---------------- TASK BOARD ---------------- #

with tab5:

    st.header("Department Task Board")

    if st.session_state.tasks:

        pending, progress, completed = [], [], []

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
                st.write(f"{t['Department']} - {t['Task']}")

        with col2:

            st.subheader("In Progress")

            for t in progress:
                st.write(f"{t['Department']} - {t['Task']}")

        with col3:

            st.subheader("Completed")

            for t in completed:
                st.write(f"{t['Department']} - {t['Task']}")

        st.markdown("---")

        st.subheader("Update Task Status")

        for i, task in enumerate(st.session_state.tasks):

            col1, col2, col3 = st.columns(3)

            col1.write(task["Department"])
            col2.write(task["Task"])

            new_status = col3.selectbox(
                "Status",
                ["Pending","In Progress","Completed"],
                index=["Pending","In Progress","Completed"].index(task["Status"]),
                key=f"task_{i}"
            )

            if new_status != task["Status"]:

                if new_status == "In Progress":
                    st.session_state.alerts.append(
                        f"⚡ {task['Department']} started task '{task['Task']}'"
                    )

                if new_status == "Completed":
                    st.session_state.alerts.append(
                        f"✅ {task['Department']} completed task '{task['Task']}'"
                    )

                st.session_state.tasks[i]["Status"] = new_status

    else:

        st.info("No tasks created yet")

# ---------------- COURIER TRACKER ---------------- #

with tab6:

    st.header("Courier Tracking")

    courier = st.selectbox(
        "Courier Company",
        ["Blue Dart","DTDC","Delhivery","DHL","FedEx"]
    )

    awb = st.text_input("AWB Number")

    destination = st.text_input("Destination")

    if st.button("Track Shipment"):

        st.success("Tracking information fetched")

        st.write("Status: In Transit")

        st.write("Expected Delivery: 3 Days")