import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime
import random
import string
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Rental Management System", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: #ffffff;
    }

    [data-testid="stSidebar"] {
        background-color: #0f2027;
        border-right: 1px solid #2c5364;
    }

    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    [data-testid="stForm"], div.stDataFrame, div.stMetric {
        background-color: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 10px;
    }

    [data-testid="stMetricLabel"] {
        color: #a0c4ff !important;
        font-size: 13px !important;
    }

    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 24px !important;
        font-weight: 700 !important;
    }

    .stButton > button {
        background: linear-gradient(90deg, #00c853, #009624);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        font-size: 15px;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,200,83,0.4);
    }

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        background-color: rgba(255,255,255,0.08) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 8px !important;
    }

    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    .stAlert {
        border-radius: 10px !important;
    }

    .stDataFrame {
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        ssl_disabled=False
    )

def generate_unique_code(cursor):
    while True:
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        unique_code = f"TNT-A{random_suffix}"
        cursor.execute("SELECT id FROM tenants WHERE unique_code = %s", (unique_code,))
        if not cursor.fetchone():
            return unique_code

def process_incoming_payment(unique_code, amount, target_month):
    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)
    cursor.execute("SELECT id, tenant_name FROM tenants WHERE unique_code = %s", (unique_code,))
    result = cursor.fetchone()
    if result:
        tenant_id, tenant_name = result
        cursor.execute(
            "INSERT INTO payments (tenant_id, amount_paid, date_paid, month_paid) VALUES (%s, %s, %s, %s)", 
            (tenant_id, amount, datetime.now().strftime('%Y-%m-%d'), target_month)
        )
        conn.commit()
        msg = f"✅ Matched payment of KES {amount:,} to {tenant_name} for {target_month}"
    else:
        msg = f"❌ Error: No tenant found with code {unique_code}"
    cursor.close()
    conn.close()
    return msg

current_date = datetime.now().strftime('%Y-%m-%d')
current_year = datetime.now().year
months_list = [
    "January", "February", "March", "April", "May", "June", 
    "July", "August", "September", "October", "November", "December"
]
month_options = [f"{m} {current_year}" for m in months_list]

st.sidebar.title("🏢 Rental System")
page = st.sidebar.radio("Navigate To:", [
    "📊 Dashboard", 
    "👤 Register Tenant", 
    "💰 Log Payment", 
    "🚪 Manage Rooms",
    "💳 Payment Cards",
    "❌ Remove Tenant",
    "🔔 Notify Tenants"
])

if page == "📊 Dashboard":
    st.title("Financial Dashboard")
    conn = get_db_connection()
    st.subheader("Filter Ledger by Month")
    selected_dash_month = st.selectbox("Select Month to View", options=month_options, index=datetime.now().month - 1)
    query = """
    SELECT 
        tenants.tenant_name AS 'Name', 
        tenants.unique_code AS 'Code', 
        rooms.room_number AS 'Room', 
        rooms.monthly_rent AS 'Expected Rent', 
        COALESCE(SUM(CASE WHEN payments.month_paid = %s THEN payments.amount_paid ELSE 0 END), 0) AS 'Total Paid',
        (rooms.monthly_rent - COALESCE(SUM(CASE WHEN payments.month_paid = %s THEN payments.amount_paid ELSE 0 END), 0)) AS 'Balance',
        %s AS 'Month'
    FROM tenants
    JOIN rooms ON tenants.room_id = rooms.id
    LEFT JOIN payments ON tenants.id = payments.tenant_id
    GROUP BY tenants.id, tenants.tenant_name, tenants.unique_code, rooms.room_number, rooms.monthly_rent;
    """
    df = pd.read_sql(query, conn, params=(selected_dash_month, selected_dash_month, selected_dash_month))
    conn.close()
    if not df.empty:
        df['Expected Rent'] = df['Expected Rent'].astype(float).round(2)
        df['Total Paid'] = df['Total Paid'].astype(float).round(2)
        df['Balance'] = df['Balance'].astype(float).round(2)
        total_arrears = df[df['Balance'] > 0]['Balance'].sum()
        total_overpayments = abs(df[df['Balance'] < 0]['Balance'].sum())
        unpaid_rooms_count = df[df['Balance'] > 0].shape[0]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label=f"⚠️ Arrears ({selected_dash_month})", value=f"KES {total_arrears:,.2f}")
        with col2:
            st.metric(label=f"💰 Overpayments ({selected_dash_month})", value=f"KES {total_overpayments:,.2f}")
        with col3:
            st.metric(label="👤 Rooms with Balances", value=f"{unpaid_rooms_count} Units")
        st.write("---")
        st.subheader(f"Live Tenant Ledger Status — {selected_dash_month}")
        def highlight_rows(row):
            if row['Balance'] == 0:
                return ['background-color: #d4edda; color: #155724;'] * len(row)
            elif row['Balance'] < 0:
                return ['background-color: #d1ecf1; color: #0c5460;'] * len(row)
            else:
                return ['background-color: #f8d7da; color: #721c24;'] * len(row)
        styled_df = df.style.format({
            'Expected Rent': 'KES {:,.2f}',
            'Total Paid': 'KES {:,.2f}',
            'Balance': 'KES {:,.2f}'
        }).apply(highlight_rows, axis=1)
        st.dataframe(styled_df, width='stretch')
    else:
        st.info("No active tenancies recorded. Go to 'Register Tenant' to log data.")

elif page == "👤 Register Tenant":
    st.title("Register New Tenant")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, room_number FROM rooms;")
    rooms = {f"{r[1]}": r[0] for r in cursor.fetchall()}
    with st.form("new_tenant", clear_on_submit=True):
        name = st.text_input("Name")
        phone = st.text_input("Phone Number")
        room = st.selectbox("Room", options=list(rooms.keys()))
        if st.form_submit_button("Register"):
            code = generate_unique_code(cursor)
            cursor.execute("INSERT INTO tenants (tenant_name, phone_number, room_id, unique_code, start_date) VALUES (%s, %s, %s, %s, %s)",
                           (name, phone, rooms[room], code, current_date))
            conn.commit()
            st.success(f"Registered! Tenant Code: {code}")
    conn.close()

elif page == "💰 Log Payment":
    st.title("Simulate Incoming Payment")
    with st.form("manual_payment", clear_on_submit=True):
        code_input = st.text_input("Enter Unique Code (e.g. TNT-A1B2)")
        amount_input = st.number_input("Amount Paid (KES)", min_value=0, step=500)
        target_month_input = st.selectbox("Assign Payment to Month:", options=month_options, index=datetime.now().month - 1)
        if st.form_submit_button("Process Payment"):
            result = process_incoming_payment(code_input, amount_input, target_month_input)
            st.write(result)

elif page == "🚪 Manage Rooms":
    st.title("Manage Units")
    conn = get_db_connection()
    cursor = conn.cursor()
    with st.form("room_form", clear_on_submit=True):
        name = st.text_input("Room Designation")
        rent = st.number_input("Monthly Rent", min_value=0)
        if st.form_submit_button("Add Room"):
            cursor.execute("INSERT INTO rooms (room_number, monthly_rent) VALUES (%s, %s);", (name, rent))
            conn.commit()
            st.success("Room added!")
    conn.close()

elif page == "💳 Payment Cards":
    st.title("Generate Payment Instruction Card")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, tenant_name, unique_code FROM tenants;")
    tenants = cursor.fetchall()
    tenant_options = {f"{t[1]} ({t[2]})": t[0] for t in tenants}
    selected = st.selectbox("Select Tenant", options=list(tenant_options.keys()))
    if st.button("Generate Card"):
        t_id = tenant_options[selected]
        cursor.execute("SELECT tenant_name, unique_code FROM tenants WHERE id = %s", (t_id,))
        name, code = cursor.fetchone()
        st.markdown(f"""
        <div style="border: 2px solid #00c853; padding: 30px; border-radius: 12px; background: rgba(0,200,83,0.08); text-align: center;">
            <h2 style="color: #00c853;">RENT PAYMENT INSTRUCTIONS</h2>
            <hr style="border-top: 1px solid rgba(255,255,255,0.2);">
            <h3 style="color: #ffffff;">Paybill Number: <span style="color: #00c853; font-weight: bold;">1234567</span></h3>
            <h3 style="color: #ffffff;">Account Number: <span style="color: #00c853; font-weight: bold;">{code}</span></h3>
            <br>
            <p style="color: #ffffff;"><strong>Tenant:</strong> {name}</p>
        </div>
        """, unsafe_allow_html=True)
    conn.close()

elif page == "❌ Remove Tenant":
    st.title("Remove Permanent Leavers")
    st.warning("⚠️ CRITICAL WARNING: Deleting a tenant will permanently erase their registration details and ALL associated payment history. This cannot be undone.")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, tenant_name, unique_code FROM tenants;")
    tenants = cursor.fetchall()
    if tenants:
        tenant_options = {f"{t[1]} ({t[2]})": t[0] for t in tenants}
        selected_tenant = st.selectbox("Select Tenant to Permanently Delete", options=list(tenant_options.keys()))
        confirm_check = st.checkbox("I confirm that this tenant has permanently left and I want to erase all their records.")
        if st.button("Permanently Erase Tenant Record", type="primary"):
            if confirm_check:
                target_id = tenant_options[selected_tenant]
                try:
                    cursor.execute("DELETE FROM payments WHERE tenant_id = %s;", (target_id,))
                    cursor.execute("DELETE FROM tenants WHERE id = %s;", (target_id,))
                    conn.commit()
                    st.success(f"💥 {selected_tenant} has been deleted.")
                    st.rerun()
                except mysql.connector.Error as err:
                    conn.rollback()
                    st.error(f"Database error: {err}")
            else:
                st.error("Please check the confirmation box before deleting.")
    else:
        st.info("No tenants in the database.")
    conn.close()

elif page == "🔔 Notify Tenants":
    st.title("Send Rent Due Reminders")
    current_month = datetime.now().strftime("%B %Y")
    st.info(f"This will send SMS reminders to all tenants with an outstanding balance for **{current_month}**.")
    conn = get_db_connection()
    query = """
        SELECT t.tenant_name, t.phone_number, r.room_number, r.monthly_rent,
               COALESCE(SUM(p.amount_paid), 0) AS total_paid
        FROM tenants t
        JOIN rooms r ON t.room_id = r.id
        LEFT JOIN payments p ON t.id = p.tenant_id AND p.month_paid = %s
        GROUP BY t.id, t.tenant_name, t.phone_number, r.room_number, r.monthly_rent
        HAVING (r.monthly_rent - total_paid) > 0;
    """
    df = pd.read_sql(query, conn, params=(current_month,))
    conn.close()
    if df.empty:
        st.success(f"🎉 All tenants are fully paid for {current_month}. No reminders needed!")
    else:
        df['Balance'] = df['monthly_rent'].astype(float) - df['total_paid'].astype(float)
        df = df.rename(columns={
            "tenant_name": "Tenant", "phone_number": "Phone",
            "room_number": "Room", "monthly_rent": "Rent", "total_paid": "Paid"
        })
        st.warning(f"⚠️ {len(df)} tenant(s) have outstanding balances:")
        st.dataframe(df[["Tenant", "Room", "Rent", "Paid", "Balance"]])
        if st.button("📨 Send SMS Reminders to All", type="primary"):
            from notifier import check_and_notify_due_payments
            results = check_and_notify_due_payments()
            for r in results:
                icon = "✅" if r["sms_sent"] else "❌"
                st.write(f"{icon} {r['name']} — Room {r['room']} — KES {r['balance']:,.0f} balance")