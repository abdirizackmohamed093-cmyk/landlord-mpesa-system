import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime
import random
import string
import os
import bcrypt
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
        background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
        color: #ffffff;
    }

    [data-testid="stSidebar"] {
        background-color: #0d0d1a;
        border-right: 1px solid #00c853;
    }

    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    /* ALL labels visible */
    label, .stTextInput label, .stNumberInput label,
    .stSelectbox label, .stCheckbox label,
    .stRadio label, div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        font-size: 14px !important;
        font-weight: 600 !important;
    }

    h1, h2, h3, h4, h5 {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* Input fields — dark background, white text */
    input[type="text"], input[type="password"], input[type="number"], input[type="email"] {
        background-color: #1e2a3a !important;
        color: #ffffff !important;
        border: 1px solid #00c853 !important;
        border-radius: 8px !important;
    }

    /* Selectbox */
    .stSelectbox > div > div {
        background-color: #1e2a3a !important;
        color: #ffffff !important;
        border: 1px solid #00c853 !important;
        border-radius: 8px !important;
    }

    /* Dropdown options */
    [data-baseweb="select"] * {
        background-color: #1e2a3a !important;
        color: #ffffff !important;
    }

    /* Form container */
    [data-testid="stForm"] {
        background-color: rgba(255,255,255,0.05);
        border: 1px solid rgba(0,200,83,0.3);
        border-radius: 12px;
        padding: 20px;
    }

    /* Metrics */
    [data-testid="stMetricLabel"] {
        color: #a0c4ff !important;
        font-size: 13px !important;
    }

    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 24px !important;
        font-weight: 700 !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #00c853, #009624);
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        font-size: 15px;
        transition: all 0.3s ease;
        width: 100%;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,200,83,0.4);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        color: #ffffff !important;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        color: #00c853 !important;
        border-bottom: 2px solid #00c853;
    }

    /* Alert boxes */
    .stAlert {
        border-radius: 10px !important;
    }

    /* Dataframe */
    .stDataFrame {
        border-radius: 10px !important;
    }

    /* Checkbox */
    .stCheckbox > label {
        color: #ffffff !important;
    }

    /* Placeholder text */
    ::placeholder {
        color: #aaaaaa !important;
    }

    /* Radio buttons */
    .stRadio > div > label {
        color: #ffffff !important;
    }

    /* Subheader */
    .stSubheader {
        color: #ffffff !important;
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


def generate_unique_code(cursor, landlord_id):
    while True:
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        unique_code = f"TNT-A{random_suffix}"
        cursor.execute("SELECT id FROM tenants WHERE unique_code = %s AND landlord_id = %s", (unique_code, landlord_id))
        if not cursor.fetchone():
            return unique_code


def process_incoming_payment(unique_code, amount, target_month, landlord_id):
    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)
    cursor.execute("SELECT id, tenant_name FROM tenants WHERE unique_code = %s AND landlord_id = %s", (unique_code, landlord_id))
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


def register_landlord(full_name, email, password):
    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)
    cursor.execute("SELECT id FROM landlords WHERE email = %s", (email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return False, "Email already registered."
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    cursor.execute("INSERT INTO landlords (full_name, email, password) VALUES (%s, %s, %s)",
                   (full_name, email, hashed))
    conn.commit()
    cursor.close()
    conn.close()
    return True, "Account created successfully! Please log in."


def login_landlord(email, password):
    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)
    cursor.execute("SELECT id, full_name, password FROM landlords WHERE email = %s", (email,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        landlord_id, full_name, hashed = result
        if bcrypt.checkpw(password.encode(), hashed.encode()):
            return True, landlord_id, full_name
    return False, None, None


if "landlord_id" not in st.session_state:
    st.session_state.landlord_id = None
if "landlord_name" not in st.session_state:
    st.session_state.landlord_name = None


if st.session_state.landlord_id is None:
    st.markdown("<h1 style='text-align:center; color:#00c853;'>🏢 Rental Management System</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#aaaaaa;'>Manage your properties professionally</p>", unsafe_allow_html=True)
    st.write("")

    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

    with tab1:
        st.markdown("### Welcome back!")
        with st.form("login_form"):
            st.markdown("**Email Address**")
            email = st.text_input("", placeholder="Enter your email", key="login_email")
            st.markdown("**Password**")
            password = st.text_input("", placeholder="Enter your password", type="password", key="login_pass")
            if st.form_submit_button("Login →"):
                success, landlord_id, full_name = login_landlord(email, password)
                if success:
                    st.session_state.landlord_id = landlord_id
                    st.session_state.landlord_name = full_name
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

    with tab2:
        st.markdown("### Create your account")
        with st.form("register_form"):
            st.markdown("**Full Name**")
            full_name = st.text_input("", placeholder="Enter your full name", key="reg_name")
            st.markdown("**Email Address**")
            email = st.text_input("", placeholder="Enter your email", key="reg_email")
            st.markdown("**Password**")
            password = st.text_input("", placeholder="Create a password", type="password", key="reg_pass")
            st.markdown("**Confirm Password**")
            confirm = st.text_input("", placeholder="Confirm your password", type="password", key="reg_confirm")
            if st.form_submit_button("Create Account →"):
                if password != confirm:
                    st.error("Passwords do not match.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    success, msg = register_landlord(full_name, email, password)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)

else:
    landlord_id = st.session_state.landlord_id
    landlord_name = st.session_state.landlord_name

    current_date = datetime.now().strftime('%Y-%m-%d')
    current_year = datetime.now().year
    months_list = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    month_options = [f"{m} {current_year}" for m in months_list]

    st.sidebar.title("🏢 Rental System")
    st.sidebar.write(f"👋 **{landlord_name}**")
    st.sidebar.write("---")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.landlord_id = None
        st.session_state.landlord_name = None
        st.rerun()

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
        st.title("📊 Financial Dashboard")
        conn = get_db_connection()
        st.markdown("**Select Month to View**")
        selected_dash_month = st.selectbox("", options=month_options, index=datetime.now().month - 1)
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
        WHERE tenants.landlord_id = %s
        GROUP BY tenants.id, tenants.tenant_name, tenants.unique_code, rooms.room_number, rooms.monthly_rent;
        """
        df = pd.read_sql(query, conn, params=(selected_dash_month, selected_dash_month, selected_dash_month, landlord_id))
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
                st.metric(label=f"⚠️ Arrears", value=f"KES {total_arrears:,.2f}")
            with col2:
                st.metric(label=f"💰 Overpayments", value=f"KES {total_overpayments:,.2f}")
            with col3:
                st.metric(label="👤 Rooms with Balances", value=f"{unpaid_rooms_count} Units")
            st.write("---")
            st.subheader(f"Tenant Ledger — {selected_dash_month}")
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
        st.title("👤 Register New Tenant")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, room_number FROM rooms WHERE landlord_id = %s;", (landlord_id,))
        rooms = {f"{r[1]}": r[0] for r in cursor.fetchall()}
        with st.form("new_tenant", clear_on_submit=True):
            st.markdown("**Full Name**")
            name = st.text_input("", placeholder="Enter tenant name", key="t_name")
            st.markdown("**Phone Number**")
            phone = st.text_input("", placeholder="e.g. 0712345678", key="t_phone")
            st.markdown("**Select Room**")
            room = st.selectbox("", options=list(rooms.keys()), key="t_room")
            if st.form_submit_button("Register Tenant →"):
                code = generate_unique_code(cursor, landlord_id)
                cursor.execute("INSERT INTO tenants (tenant_name, phone_number, room_id, unique_code, start_date, landlord_id) VALUES (%s, %s, %s, %s, %s, %s)",
                               (name, phone, rooms[room], code, current_date, landlord_id))
                conn.commit()
                st.success(f"✅ Registered! Tenant Code: **{code}**")
        conn.close()

    elif page == "💰 Log Payment":
        st.title("💰 Log Payment")
        with st.form("manual_payment", clear_on_submit=True):
            st.markdown("**Tenant Unique Code**")
            code_input = st.text_input("", placeholder="e.g. TNT-A1B2", key="p_code")
            st.markdown("**Amount Paid (KES)**")
            amount_input = st.number_input("", min_value=0, step=500, key="p_amount")
            st.markdown("**Assign to Month**")
            target_month_input = st.selectbox("", options=month_options, index=datetime.now().month - 1, key="p_month")
            if st.form_submit_button("Process Payment →"):
                result = process_incoming_payment(code_input, amount_input, target_month_input, landlord_id)
                st.write(result)

    elif page == "🚪 Manage Rooms":
        st.title("🚪 Manage Units")
        conn = get_db_connection()
        cursor = conn.cursor()
        with st.form("room_form", clear_on_submit=True):
            st.markdown("**Room Name**")
            name = st.text_input("", placeholder="e.g. Room 01", key="r_name")
            st.markdown("**Monthly Rent (KES)**")
            rent = st.number_input("", min_value=0, key="r_rent")
            if st.form_submit_button("Add Room →"):
                cursor.execute("INSERT INTO rooms (room_number, monthly_rent, landlord_id) VALUES (%s, %s, %s);",
                               (name, rent, landlord_id))
                conn.commit()
                st.success("✅ Room added!")
        conn.close()

    elif page == "💳 Payment Cards":
        st.title("💳 Payment Instruction Card")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, tenant_name, unique_code FROM tenants WHERE landlord_id = %s;", (landlord_id,))
        tenants = cursor.fetchall()
        tenant_options = {f"{t[1]} ({t[2]})": t[0] for t in tenants}
        st.markdown("**Select Tenant**")
        selected = st.selectbox("", options=list(tenant_options.keys()))
        if st.button("Generate Card →"):
            t_id = tenant_options[selected]
            cursor.execute("SELECT tenant_name, unique_code FROM tenants WHERE id = %s", (t_id,))
            name, code = cursor.fetchone()
            st.markdown(f"""
            <div style="border: 2px solid #00c853; padding: 30px; border-radius: 12px; background: rgba(0,200,83,0.08); text-align: center; margin-top: 20px;">
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
        st.title("❌ Remove Tenant")
        st.warning("⚠️ This will permanently erase the tenant and all their payment history.")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, tenant_name, unique_code FROM tenants WHERE landlord_id = %s;", (landlord_id,))
        tenants = cursor.fetchall()
        if tenants:
            tenant_options = {f"{t[1]} ({t[2]})": t[0] for t in tenants}
            st.markdown("**Select Tenant**")
            selected_tenant = st.selectbox("", options=list(tenant_options.keys()))
            confirm_check = st.checkbox("I confirm I want to permanently delete this tenant.")
            if st.button("Delete Tenant →", type="primary"):
                if confirm_check:
                    target_id = tenant_options[selected_tenant]
                    try:
                        cursor.execute("DELETE FROM payments WHERE tenant_id = %s;", (target_id,))
                        cursor.execute("DELETE FROM tenants WHERE id = %s;", (target_id,))
                        conn.commit()
                        st.success(f"✅ {selected_tenant} has been deleted.")
                        st.rerun()
                    except mysql.connector.Error as err:
                        conn.rollback()
                        st.error(f"Database error: {err}")
                else:
                    st.error("Please check the confirmation box first.")
        else:
            st.info("No tenants in the database.")
        conn.close()

    elif page == "🔔 Notify Tenants":
        st.title("🔔 Send Rent Reminders")
        current_month = datetime.now().strftime("%B %Y")
        st.info(f"Sending SMS reminders to tenants with outstanding balances for **{current_month}**.")
        conn = get_db_connection()
        query = """
            SELECT t.tenant_name, t.phone_number, r.room_number, r.monthly_rent,
                   COALESCE(SUM(p.amount_paid), 0) AS total_paid
            FROM tenants t
            JOIN rooms r ON t.room_id = r.id
            LEFT JOIN payments p ON t.id = p.tenant_id AND p.month_paid = %s
            WHERE t.landlord_id = %s
            GROUP BY t.id, t.tenant_name, t.phone_number, r.room_number, r.monthly_rent
            HAVING (r.monthly_rent - total_paid) > 0;
        """
        df = pd.read_sql(query, conn, params=(current_month, landlord_id))
        conn.close()
        if df.empty:
            st.success(f"🎉 All tenants are fully paid for {current_month}!")
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