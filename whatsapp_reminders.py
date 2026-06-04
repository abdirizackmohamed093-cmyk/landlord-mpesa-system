import mysql.connector
import pywhatkit
import time

# 1. Connect to your Rental Database
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="ilovechelseafootballclub",
    database="rental_db"
)
cursor = connection.cursor()

# 2. Get tenants who owe money
query = """
SELECT tenants.tenant_name, tenants.phone_number, rooms.room_number, rooms.monthly_rent, COALESCE(payments.amount_paid, 0)
FROM tenants
INNER JOIN rooms ON tenants.room_id = rooms.id
LEFT JOIN payments ON tenants.id = payments.tenant_id;
"""
cursor.execute(query)

print("=== STARTING WHATSAPP BALANCES AUTOMATION ===")
print("Make sure you are logged into WhatsApp Web on your default browser!")
print("-----------------------------------------------------------------")

for row in cursor.fetchall():
    tenant_name = row[0]
    phone_number = row[1]  # Ensure numbers in DB look like '+2547XXXXXXXX'
    room_number = row[2]
    monthly_rent = row[3]
    amount_paid = row[4]
    
    balance_owed = monthly_rent - amount_paid
    
    if balance_owed > 0:
        # Create the custom message text
        message = f"Habari {tenant_name}, this is a friendly reminder that your rent balance for {room_number} is KES {balance_owed:,}. Please clear as soon as possible. Thank you!"
        
        print(f"Sending message to {tenant_name} ({phone_number})...")
        
        try:
            # sendwhatmsg_instantly opens your browser, types the text, and sends it.
            # wait_time=15 gives the browser 15 seconds to load WhatsApp Web before typing.
            # tab_close=True automatically closes the browser tab when done!
            pywhatkit.sendwhatmsg_instantly(
                phone_no=phone_number, 
                message=message, 
                wait_time=15, 
                tab_close=True
            )
            print(f"✅ Dispatched successfully to {tenant_name}!")
            
            # Give the system a 10-second break before doing the next tenant 
            # so your browser doesn't get overwhelmed.
            time.sleep(10)
            
        except Exception as e:
            print(f"❌ Failed to process WhatsApp for {tenant_name}: {e}")

# Clean up connections
cursor.close()
connection.close()
print("\n=== ALL REMINDERS PROCESSED ===")