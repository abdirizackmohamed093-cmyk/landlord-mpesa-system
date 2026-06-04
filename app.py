from db_utils import process_incoming_payment

# Now you can just call it in your app like this:
# process_incoming_payment(code, amount)
    
import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime
import random
import string

# Set up page configurations
st.set_page_config(page_title="Rental Management System", layout="wide")

# Database Connection Helper Function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="ilovechelseafootballclub",
        database="rental_db"
    )

# Function to generate a unique 4-character alphanumeric code
def generate_unique_code(cursor):
    while True:
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        unique_code = f"TNT-{random_suffix}"
        cursor.execute("SELECT id FROM tenants WHERE unique_code = %s", (unique_code,))
        if not cursor.fetchone():
            return unique_code

# The "Brain" that matches a code to a tenant
def process_incoming_payment(unique_code, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, tenant_name FROM tenants WHERE unique_code = %s", (unique_code,))
    result = cursor.fetchone()
    if result:
        tenant_id, tenant_name = result
        cursor.execute("INSERT INTO payments (tenant_id, amount_paid, date_paid) VALUES (%s, %s, %s)", 
                       (tenant_id, amount, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        msg = f"✅ Matched payment of KES {amount:,} to {tenant_name}"
    else:
        msg = f"❌ Error: No tenant found with code {unique_code}"
    cursor.close()
    conn.close()
    return msg

# Get current date
current_date = datetime.now().strftime('%Y-%m-%d')

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🏢 Rental System")
page = st.sidebar.radio("Navigate To:", [
    "📊 Dashboard", 
    "👤 Register Tenant", 
    "💰 Log Payment", 
    "🚪 Manage Rooms",
    "💳 Payment Cards"
])

# --- PAGE: DASHBOARD ---
if page == "📊 Dashboard":
    st.title("Financial Dashboard")
    conn = get_db_connection()
    query = """
    SELECT tenants.tenant_name AS 'Name', tenants.unique_code AS 'Code', 
           rooms.room_number AS 'Room', rooms.monthly_rent AS 'Rent', 
           COALESCE(SUM(payments.amount_paid), 0) as 'Total Paid'
    FROM tenants
    JOIN rooms ON tenants.room_id = rooms.id
    LEFT JOIN payments ON tenants.id = payments.tenant_id
    GROUP BY tenants.id;
    """
    df = pd.read_sql(query, conn)
    st.dataframe(df, use_container_width=True)
    conn.close()

# --- PAGE: REGISTER TENANT ---
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

# --- PAGE: LOG PAYMENT ---
elif page == "💰 Log Payment":
    st.title("Simulate Incoming Payment")
    with st.form("manual_payment", clear_on_submit=True):
        code_input = st.text_input("Enter Unique Code (e.g. TNT-A1B2)")
        amount_input = st.number_input("Amount Paid (KES)", min_value=0, step=500)
        if st.form_submit_button("Process Payment"):
            result = process_incoming_payment(code_input, amount_input)
            st.write(result)

# --- PAGE: MANAGE ROOMS ---
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

# --- PAGE: PAYMENT CARDS ---
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
        <div style="border: 2px solid #4CAF50; padding: 20px; border-radius: 10px; background-color: #f9f9f9; text-align: center;">
            <h2>PAYMENT INSTRUCTIONS</h2>
            <p>Use the following details for your monthly rent:</p>
            <h3>Paybill: 123456</h3>
            <p>Account Number:</p>
            <h1 style="background: #e8f5e9; padding: 10px;">{code}</h1>
            <p><strong>Tenant:</strong> {name}</p>
        </div>
        """, unsafe_allow_html=True)
    conn.close()