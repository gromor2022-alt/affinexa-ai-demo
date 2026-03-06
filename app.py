import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(page_title="Banares Beads Operations", layout="wide")

# ---------------- STYLE ---------------- #

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

        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):

            if u == "demo" and p == "AffiNexa@123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials")

        st.stop()

login()

# ---------------- SESSION ---------------- #

if "df" not in st.session_state:
    st.session_state.df = None

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "alerts" not in st.session_state:
    st.session_state.alerts = []

if "bom" not in st.session_state:
    st.session_state.bom = None

# ---------------- HEADER ---------------- #

st.title("Banares Beads Operations Control System")

st.markdown("Sales Contract → *BOM Generation → Department Tasks → Dispatch Tracking*")

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

    orders = len(st.session_state.df) if st.session_state.df is not None else 0
    tasks = len(st.session_state.tasks)

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Products Loaded", orders)
    c2.metric("Department Tasks", tasks)
    c3.metric("Active Shipments", 2)
    c4.metric("Departments", 5)

    st.markdown("---")

    st.subheader("Recent Alerts")

    if st.session_state.alerts:
        for a in st.session_state.alerts[-5:]:
            st.info(a)
    else:
        st.write("No alerts yet")

# ---------------- UPLOAD EXCEL ---------------- #

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

        df.columns = df.columns.str.strip()

        required = ["Item","ItmSize","itmColor","ReqQty"]

        if all(c in df.columns for c in required):

            bom = df.groupby(
                ["Item","ItmSize","itmColor"]
            )["ReqQty"].sum().reset_index()

            st.session_state.bom = bom

            st.subheader("Generated BOM")

            st.dataframe(bom)

            if st.button("Generate Department Tasks from BOM"):

                for _,row in bom.iterrows():

                    product = f"{row['Item']} {row['ItmSize']} {row['itmColor']}"

                    qty = row["ReqQty"]

                    departments = [
                        ("Procurement", f"Procure materials for {product} ({qty})"),
                        ("Polishing", f"Polish batch for {product}"),
                        ("Packaging", f"Pack items for {product}"),
                        ("Dispatch", f"Dispatch order for {product}")
                    ]

                    for dept,task in departments:

                        st.session_state.tasks.append({
                            "Department":dept,
                            "Task":task,
                            "Status":"Pending"
                        })

                st.success("Department tasks created from BOM")

        else:

            st.warning("Excel columns not matching expected structure")

    else:

        st.info("Upload Sales Contract first")

# ---------------- PRODUCT VIEW ---------------- #

with tab4:

    st.header("Product Overview")

    if st.session_state.df is not None:

        df = st.session_state.df

        show_cols = [
            "Item",
            "ItmShape",
            "ItmSize",
            "itmColor",
            "ReqQty",
            "QtyUOM"
        ]

        available = [c for c in show_cols if c in df.columns]

        st.dataframe(df[available])

    else:

        st.info("Upload Excel first")

# ---------------- TASK BOARD ---------------- #

with tab5:

    st.header("Department Task Board")

    if st.session_state.tasks:

        pending,progress,done = [],[],[]

        for t in st.session_state.tasks:

            if t["Status"]=="Pending":
                pending.append(t)
            elif t["Status"]=="In Progress":
                progress.append(t)
            else:
                done.append(t)

        col1,col2,col3 = st.columns(3)

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

            for t in done:
                st.write(f"{t['Department']} - {t['Task']}")

        st.markdown("---")

        st.subheader("Update Status")

        for i,t in enumerate(st.session_state.tasks):

            c1,c2,c3 = st.columns(3)

            c1.write(t["Department"])
            c2.write(t["Task"])

            new = c3.selectbox(
                "Status",
                ["Pending","In Progress","Completed"],
                index=["Pending","In Progress","Completed"].index(t["Status"]),
                key=f"task{i}"
            )

            if new != t["Status"]:

                if new=="In Progress":
                    st.session_state.alerts.append(f"{t['Department']} started {t['Task']}")

                if new=="Completed":
                    st.session_state.alerts.append(f"{t['Department']} completed {t['Task']}")

                st.session_state.tasks[i]["Status"] = new

    else:

        st.info("No tasks created yet")

# ---------------- COURIER TRACKING ---------------- #

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