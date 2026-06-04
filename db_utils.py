import mysql.connector

# Centralized connection settings
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="your_username",
        password="your_password",
        database="your_database_name"
    )

def process_incoming_payment(unique_code, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Your specific SQL query to update the payments table
    query = "INSERT INTO payments (unique_code, amount) VALUES (%s, %s)"
    cursor.execute(query, (unique_code, amount))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Database updated for {unique_code}")