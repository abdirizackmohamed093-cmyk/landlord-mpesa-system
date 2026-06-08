import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime
import random
import string
import os
from dotenv import load_dotenv

load_dotenv()

# Set up page configurations with a premium title
st.set_page_config(page_title="AuraProp | Premium Rental Analytics", layout="wide")

# --- EXECUTIVE UI STYLING ENGINE ---
st.markdown("""
    <style>
        /* Main App Background Configuration */
        .stApp {
            background-color: #f4f6f9;
        }
        
        /* Premium Sidebar Overrides */
        [data-testid="stSidebar"] {
            background-color: #111827 !important;
        }
        [data-testid="stSidebar"] *, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
            color: #f3f4f6 !important;
            font-weight: 500;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: #ffffff !important;
            letter-spacing: 0.5px;
        }
        
        /* Clean Up Main Body Text Typography */
        h1 {
            color: #1f2937 !important;
            font-weight: 700 !important;
            font-size: 2.2rem !important;
            padding-bottom: 10px;
        }
        h2, h3 {
            color: #374151 !important;
            font-weight: 600 !important;
        }
        
        /* Custom Premium Executive Metric Cards */
        .metric-card {
            background-color: #ffffff;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            border-left: 5px solid #10b981; /* Default Safe Green */
            margin-bottom: 15px;
        }
        .metric-card.arrears {
            border-left-color: #ef4444; /* Corporate Warning Red */
        }
        .metric-card.neutral {
            border-left-color: #3b82f6; /* Corporate Info Blue */
        }
        .metric-label {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #6b7280;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #111827;
        }
        
        /* Form Card Custom Styling */
        div[data-testid="stForm"] {
            background-color: #ffffff !important;
            padding: 30px !important;
            border-radius: 12px !important;
            border: none !important;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05) !important;
        }
        
        /* Clean Up Standard Streamlit Horizontal Line */
        hr {
            margin-top: 2rem !important;
            margin-bottom: 2rem !important;
            border: 0 !important;
            border-top: 1px solid #e5e7eb !important;
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

st.sidebar.title("🏢 AuraProp Admin")
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
    
    st.markdown("### Filter Options")
    selected_dash_month = st.selectbox("Select Month to View Portal Ledger", options=month_options, index=datetime.now().month - 1, label_visibility="collapsed")
    
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
        
        # Injected Custom Executive Metric Grid
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
                <div class="metric-card arrears">
                    <div class="metric-label">⚠️ Portfolio Arrears ({selected_dash_month})</div>
                    <div class="metric-value">KES {total_arrears:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">💰 Overpayments ({selected_dash_month})</div>
                    <div class="metric-value">KES {total_overpayments:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
                <div class="metric-card neutral">
                    <div class="metric-label">👤 Unpaid Units Ledger Count</div>
                    <div class="metric-value">{unpaid_rooms_count} Units</div>
                </div>
            """, unsafe_allow_html=True)
            
        st.write("---")
        st.subheader(f"Live Tenant Ledger Status — {selected_dash_month}")
        
        # Soft corporate subtle ledger status highlights
        def highlight_rows(row):
            if row['Balance'] == 0:
                return ['background-color: #e6f4ea; color: #137333;'] * len(row) # Soft green
            elif row['Balance'] < 0:
                return ['background-color: #e8f0fe; color: #1a73e8;'] * len(row) # Soft blue
            else:
                return ['background-color: #fce8e6; color: #c5221f;'] * len(row) # Soft red
                
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
        room = st.selectbox("Room Assignment", options=list(rooms.keys()))
        if st.form_submit_button("Register System Profile"):
            code = generate_unique_code(cursor)
            cursor.execute("INSERT INTO tenants (tenant_name, phone_number, room_id, unique_code, start_date) VALUES (%s, %s, %s, %s, %s)",
                           (name, phone, rooms[room], code, current_date))
            conn.commit()
            st.success(f"Tenant Account Configured! Secure Assignment Reference: {code}")
    conn.close()

elif page == "💰 Log Payment":
    st.title("Simulate Incoming Payment")
    with st.form("manual_payment", clear_on_submit=True):
        code_input = st.text_input("Enter Tenant Reference Code (e.g. TNT-A1B2)")
        amount_input = st.number_input("Amount Paid (KES)", min_value=0, step=500)
        target_month_input = st.selectbox("Assign Payment to Month:", options=month_options, index=datetime.now().month - 1)
        if st.form_submit_button("Process Real-time Reconciliation"):
            result = process_incoming_payment(code_input, amount_input, target_month_input)
            st.write(result)

elif page == "🚪 Manage Rooms":
    st.title("Manage Units")
    conn = get_db_connection()
    cursor = conn.cursor()
    with st.form("room_form", clear_on_submit=True):
        name = st.text_input("Room Designation")
        rent = st.number_input("Fixed Monthly Rent Asset Value", min_value=0)
        if st.form_submit_button("Provision Asset Unit"):
            cursor.execute("INSERT INTO rooms (room_number, monthly_rent) VALUES (%s, %s);", (name, rent))
            conn.commit()
            st.success("Unit asset successfully provisioned into local ledger database!")
    conn.close()

elif page == "💳 Payment Cards":
    st.title("Generate Payment Instruction Card")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, tenant_name, unique_code FROM tenants;")
    tenants = cursor.fetchall()
    tenant_options = {f"{t[1]} ({t[2]})": t[0] for t in tenants}
    selected = st.selectbox("Select Target Tenant", options=list(tenant_options.keys()))
    if st.button("Generate Digital Invoice Receipt Card"):
        t_id = tenant_options[selected]
        cursor.execute("SELECT tenant_name, unique_code FROM tenants WHERE id = %s", (t_id,))
        name, code = cursor.fetchone()
        st.markdown(f"""
        <div style="border: 1px solid #e5e7eb; padding: 35px; border-radius: 12px; background-color: #ffffff; text-align: center; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);">
            <h2 style="color: #111827; font-size: 1.4rem; letter-spacing: 0.5px; font-weight: 700;">DIGITAL RENTAL ACCOUNT ESCROW</h2>
            <hr style="border-top: 1px solid #f3f4f6;">
            <p style="color: #6b7280; font-weight: 500;">Remit via Automated Lipa na M-Pesa Gateway:</p>
            <h3 style="color: #111827; margin: 10px 0;">M-Pesa Official Paybill: <span style="color: #3b82f6; font-weight: bold;">174379</span></h3>
            <h3 style="color: #111827; margin: 10px 0;">Secure Ledger Account ID: <span style="color: #3b82f6; font-weight: bold;">{code}</span></h3>
            <br>
            <p style="font-size: 0.9rem; color: #4b5563;">Assigned Asset Custodian: <strong>{name}</strong></p>
        </div>
        """, unsafe_allow_html=True)
    conn.close()

elif page == "❌ Remove Tenant":
    st.title("Remove Permanent Leavers")
    st.warning("⚠️ CRITICAL SECURITY PROTOCOL: Deleting an identity profile permanently erases linked historical registration ledger states. Process execution is absolute.")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, tenant_name, unique_code FROM tenants;")
    tenants = cursor.fetchall()
    if tenants:
        tenant_options = {f"{t[1]} ({t[2]})": t[0] for t in tenants}
        selected_tenant = st.selectbox("Select Identity Portfolio to Expunge", options=list(tenant_options.keys()))
        confirm_check = st.checkbox("I verify this tenant has formally checked out and authorize permanent record erasure.")
        if st.button("De-provision Tenant Profile Data Store", type="primary"):
            if confirm_check:
                target_id = tenant_options[selected_tenant]
                try:
                    cursor.execute("DELETE FROM payments WHERE tenant_id = %s;", (target_id,))
                    cursor.execute("DELETE FROM tenants WHERE id = %s;", (target_id,))
                    conn.commit()
                    st.success(f"Profile system wipe complete for: {selected_tenant}")
                    st.rerun()
                except mysql.connector.Error as err:
                    conn.rollback()
                    st.error(f"System Database error: {err}")
            else:
                st.error("Operation Denied: You must check the security confirmation box.")
    else:
        st.info("No active tenant identities detected inside local server storage matrices.")
    conn.close()

elif page == "🔔 Notify Tenants":
    st.title("Send Rent Due Reminders")
    current_month = datetime.now().strftime("%B %Y")
    st.info(f"System parsing scan queued for outstanding automated SMS notifications targeting **{current_month}**.")
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
        st.success(f"🎉 Asset Audit Clean: All units fully reconciled for {current_month} billing loops.")
    else:
        df['Balance'] = df['monthly_rent'].astype(float) - df['total_paid'].astype(float)
        df = df.rename(columns={
            "tenant_name": "Tenant", "phone_number": "Phone",
            "room_number": "Room", "monthly_rent": "Rent", "total_paid": "Paid"
        })
        st.warning(f"⚠️ Detected {len(df)} delinquent financial account statement balance(s):")
        st.dataframe(df[["Tenant", "Room", "Rent", "Paid", "Balance"]])
        if st.button("📨 Dispatch Overdue Notices via SMS Gateway", type="primary"):
            from notifier import check_and_notify_due_payments
            results = check_and_notify_due_payments()
            for r in results:
                icon = "✅" if r["sms_sent"] else "❌"
                st.write(f"{icon} {r['name']} — Unit {r['room']} — Statement Arrears: KES {r['balance']:,.0f}")