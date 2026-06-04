from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",          # Your MySQL username
        password="your_password",  # Your MySQL password
        database="rental_db"
    )

@app.route('/payment-callback', methods=['POST'])
def mpesa_callback():
    data = request.json
    
    print("--- LIVE SAFARICOM DATA INCOMING ---")
    print(data)
    
    # 1. Extract standard C2B values from Safaricom's layout
    trans_id = data.get('TransID')
    amount = data.get('TransAmount')
    msisdn = data.get('MSISDN')         # Customer phone number
    bill_ref = data.get('BillRefNumber') # Room number / Tenant identifier
    
    # 2. Insert payment directly into your MySQL database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            INSERT INTO payments (transaction_id, amount, phone_number, reference, payment_date)
            VALUES (%s, %s, %s, %s, %s)
        """
        # Formats current date/time to fit standard MySQL TIMESTAMP layout
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute(query, (trans_id, amount, msisdn, bill_ref, current_time))
        conn.commit()
        print(f"💰 Database Updated! Recorded {amount} KES for {bill_ref}")
        
        # Respond to Safaricom letting them know the record is stored safely
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})
        
    except mysql.connector.Error as err:
        print(f"❌ Database insertion failed: {err}")
        conn.rollback()
        return jsonify({"ResultCode": 1, "ResultDesc": "Internal Database Error"})
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(port=5000, debug=True)