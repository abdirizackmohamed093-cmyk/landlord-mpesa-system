import mysql.connector
import random    # Added for generating the code
import string    # Added for generating the code

# 1. Connect to the database
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="ilovechelseafootballclub",
    database="rental_db"
)
cursor = connection.cursor()

# Helper function to generate a unique code
def generate_unique_code(cursor):
    while True:
        # Generates a code like: TNT-A1B2
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        unique_code = f"TNT-{random_suffix}"
        
        # Verify it doesn't already exist in the database
        cursor.execute("SELECT id FROM tenants WHERE unique_code = %s", (unique_code,))
        if not cursor.fetchone():
            return unique_code

while True:
    # Display the Menu options
    print("\n=== RENTAL MANAGEMENT SYSTEM ===")
    print("1. View Dashboard Reports")
    print("2. Register a New Tenant")
    print("3. Log a Rent Payment")
    print("4. Exit System")
    
    choice = input("Select an option (1-4): ")
    
    if choice == "1":
        # ... (Your report code remains the same) ...
        pass

    elif choice == "2":
        # --- REGISTER NEW TENANT WITH UNIQUE CODE ---
        print("\n--- Register New Tenant ---")
        name = input("Enter Tenant's Full Name: ")
        phone = input("Enter Phone Number: ")
        
        while True:
            room_id = input("Enter Room ID (e.g., 1 for Room 01, 2 for Room 02): ")
            cursor.execute("SELECT id FROM rooms WHERE id = %s;", (room_id,))
            if cursor.fetchone():
                break 
            print(f"⚠️ Error: Room ID '{room_id}' does not exist.")
        
        # GENERATE CODE AND INSERT
        new_code = generate_unique_code(cursor)
        
        insert_query = """
        INSERT INTO tenants (tenant_name, phone_number, room_id, start_date, unique_code) 
        VALUES (%s, %s, %s, '2026-06-03', %s);
        """
        cursor.execute(insert_query, (name, phone, room_id, new_code))
        connection.commit() 
        print(f"\n✅ Success! {name} registered with Unique Code: {new_code}")

    elif choice == "3":
        # ... (Your payment code remains the same) ...
        pass

    elif choice == "4":
        print("\nExiting system. Goodbye!")
        break
    else:
        print("\nInvalid choice. Please enter 1, 2, 3, or 4.")

cursor.close()
connection.close()