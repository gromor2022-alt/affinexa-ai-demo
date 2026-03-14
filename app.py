import streamlit as st
import pandas as pd
import pdfplumber
import re
from datetime import datetime, timedelta

st.set_page_config(page_title="Export House Operations", layout="wide")

# ---------------- UI STYLE ---------------- #

st.markdown("""
<style>
.main {background-color:#f5f7fb;}
h1 {color:#1f4e79;}
.stMetric {background-color:white;padding:15px;border-radius:10px;border:1px solid #e6e6e6;}
</style>
""", unsafe_allow_html=True)

# ---------------- LOGIN ---------------- #

def login():

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:

        st.title("AffiNexa Demo Login")

        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")

        if st.button("Login"):

            if user == "demo" and pwd == "AffiNexa@123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials")

        st.stop()

login()

# ---------------- SIDEBAR ---------------- #

department = st.sidebar.selectbox(
    "Select Department",
    ["Director","Procurement","Polishing","Packaging","Dispatch"]
)

# ---------------- SESSION STATE ---------------- #

if "df" not in st.session_state:
    st.session_state.df = None

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "alerts" not in st.session_state:
    st.session_state.alerts = []

if "bom" not in st.session_state:
    st.session_state.bom = None

# ---------------- HEADER ---------------- #

st.title("Export House Operations Control System")

st.markdown("Sales Contract → **BOM → Department Tasks → Dispatch Tracking**")

# ---------------- TABS ---------------- #

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Dashboard",
    "Upload Sales Contract",
    "BOM Generator",
    "Product View",
    "Department Tasks",
    "Courier Tracking",
    "PDF Reader"
])

# ---------------- DASHBOARD ---------------- #

with tab1:

    st.header("Operations Dashboard")

    today = datetime.today().date()

    pending = sum(1 for t in st.session_state.tasks if t["Status"] == "Pending")
    in_progress = sum(1 for t in st.session_state.tasks if t["Status"] == "In Progress")
    completed = sum(1 for t in st.session_state.tasks if t["Status"] == "Completed")

    delayed = 0
    for t in st.session_state.tasks:
        if t["Status"] != "Completed" and today > t["Deadline"]:
            delayed += 1

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Pending Tasks", pending)
    c2.metric("In Progress", in_progress)
    c3.metric("Completed", completed)
    c4.metric("Delayed Tasks", delayed)

    st.markdown("---")

    # Deadline Alerts
    st.subheader("Alerts")

    for t in st.session_state.tasks:

        if t["Status"] != "Completed":

            days_left = (t["Deadline"] - today).days

            if days_left == 1:
                st.warning(f"⚠ Deadline approaching for {t['Department']}")

            if days_left < 0:
                st.error(f"🚨 Delay detected in {t['Department']}")

    st.markdown("---")

    # Workload Chart
    if st.session_state.tasks:

        df = pd.DataFrame(st.session_state.tasks)

        st.subheader("Department Workload")

        st.bar_chart(df["Department"].value_counts())

# ---------------- UPLOAD SALES CONTRACT ---------------- #

with tab2:

    st.header("Upload Sales Contract Excel")

    file = st.file_uploader("Upload Excel", type=["xlsx"])

    if file:

        df = pd.read_excel(file)
        df.columns = df.columns.str.strip()

        st.session_state.df = df

        st.success("Sales Contract Uploaded")

        st.dataframe(df)

# ---------------- BOM GENERATOR ---------------- #

with tab3:

    st.header("BOM Generator")

    if st.session_state.df is not None:

        df = st.session_state.df.copy()

        required = ["Item","ItmSize","itmColor","ReqQty"]

        if all(col in df.columns for col in required):

            bom = df.groupby(["Item","ItmSize","itmColor"])["ReqQty"].sum().reset_index()

            st.session_state.bom = bom

            st.dataframe(bom)

            if st.button("Generate Department Tasks from BOM"):

                for _,row in bom.iterrows():

                    product = f"{row['Item']} {row['ItmSize']} {row['itmColor']}"
                    qty = row["ReqQty"]

                    deadline = datetime.today().date() + timedelta(days=3)

                    departments = [
                        ("Procurement", f"Procure material for {product} ({qty})"),
                        ("Polishing", f"Polish batch for {product}"),
                        ("Packaging", f"Pack items for {product}"),
                        ("Dispatch", f"Dispatch order for {product}")
                    ]

                    for dept,task in departments:

                        st.session_state.tasks.append({
                            "Department":dept,
                            "Task":task,
                            "Status":"Pending",
                            "Deadline":deadline
                        })

                st.success("Department tasks created")

# ---------------- PRODUCT VIEW ---------------- #

with tab4:

    st.header("Product Overview")

    if st.session_state.df is not None:

        df = st.session_state.df

        cols = ["Item","ItmShape","ItmSize","itmColor","ReqQty","QtyUOM"]

        available = [c for c in cols if c in df.columns]

        st.dataframe(df[available])

# ---------------- TASK BOARD ---------------- #

with tab5:

    st.header("Department Task Board")

    today = datetime.today().date()

    for i, t in enumerate(st.session_state.tasks):

        # Show only relevant department tasks
        if department != "Director" and t["Department"] != department:
            continue

        c1,c2,c3,c4,c5 = st.columns([2,4,2,2,2])

        c1.write(t["Department"])
        c2.write(t["Task"])
        c3.write(f"Deadline: {t['Deadline']}")

        status = c4.selectbox(
            "Status",
            ["Pending","In Progress","Completed"],
            index=["Pending","In Progress","Completed"].index(t["Status"]),
            key=f"status_{i}"
        )

        if c5.button("Submit", key=f"submit_{i}"):

            if status != t["Status"]:

                if status == "In Progress":
                    st.session_state.alerts.append(
                        f"{t['Department']} started task"
                    )

                if status == "Completed":
                    st.session_state.alerts.append(
                        f"{t['Department']} completed task"
                    )

                st.session_state.tasks[i]["Status"] = status

                st.success("Task updated")

        if t["Status"] != "Completed" and today > t["Deadline"]:

            st.error(f"⚠ Delay detected in {t['Department']}")
# ---------------- PDF READER ---------------- #

with tab7:

    st.header("PDF Reader")

    pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if pdf:

        text = ""

        with pdfplumber.open(pdf) as pdf_file:

            for p in pdf_file.pages:

                t = p.extract_text()

                if t:
                    text += t

        st.text_area("Extracted Text", text, height=250)

        nums = re.findall(r"\b\d+\b", text)

        if nums:
            st.success(f"Detected quantity: {nums[0]}")