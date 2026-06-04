import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

# Connect to the new Aiven Cloud Database
connection = pymysql.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    ssl_verify_identity=False # Aiven requires SSL connection
)

try:
    with connection.cursor() as cursor:
        print("Successfully connected to Aiven Cloud MySQL!")
        
        # 1. Create payments table for M-Pesa webhooks
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS mpesa_payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            mpesa_code VARCHAR(50) UNIQUE NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            phone_number VARCHAR(15) NOT NULL,
            tenant_name VARCHAR(100),
            house_number VARCHAR(50),
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        print("Table 'mpesa_payments' verified/created successfully.")
        
    connection.commit()
finally:
    connection.close()