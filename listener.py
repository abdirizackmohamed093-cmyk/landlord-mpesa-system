import os
from flask import Flask, request, jsonify
import pymysql # Changed from mysql.connector for Aiven compatibility
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    # Automatically reads from your Render environment variables
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 24272)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        ssl_verify_identity=False # Aiven requires SSL
    )

@app.route('/payment-callback', methods=['POST'])
def mpesa_callback():
    data = request.json
    
    print("--- LIVE SAFARICOM DATA INCOMING ---")
    print(data)
    
    # 1. Extract values from standard Safaricom C2B payload
    trans_id = data.get('TransID')
    amount = data.get('TransAmount')
    msisdn = data.get('MSISDN')         # Customer phone number
    bill_ref = data.get('BillRefNumber') # Tenant unique code typed into Account Number
    
    if not trans_id or not amount:
        return jsonify({"ResultCode": 1, "ResultDesc": "Invalid Data"}), 400

    # 2. Insert directly into your Aiven cloud database table (mpesa_payments)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            INSERT INTO mpesa_payments (mpesa_code, amount, phone_number, tenant_name, house_number)
            VALUES (%s, %s, %s, %s, %s)
        """
        # We put the bill_ref (the tenant code) directly into the table so the background system can process it
        cursor.execute(query, (trans_id, amount, msisdn, bill_ref, bill_ref))
        conn.commit()
        print(f"💰 Database Updated! Recorded {amount} KES for Code: {bill_ref}")
        
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})
        
    except pymysql.Error as err:
        print(f"❌ Database insertion failed: {err}")
        conn.rollback()
        return jsonify({"ResultCode": 1, "ResultDesc": "Internal Database Error"}), 500
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    # Used for testing locally if needed
    app.run(port=5000, debug=True)