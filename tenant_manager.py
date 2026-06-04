import mysql.connector

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",      # Replace with your MySQL username
        password="your_password",  # Replace with your MySQL password
        database="rental_db"
    )

def archive_tenant(tenant_id):
    """Marks a tenant as Archived instead of permanently deleting them."""
    connection = connect_db()
    cursor = connection.cursor()
    
    try:
        # Step 1: Update the tenant's status
        query = "UPDATE tenants SET status = 'Archived' WHERE tenant_id = %s"
        cursor.execute(query, (tenant_id,))
        connection.commit()
        
        print(f"✅ Tenant ID {tenant_id} has been successfully archived.")
        print("💼 All past payment histories and reference details remain safe.")
        
    except mysql.connector.Error as err:
        print(f"❌ Error updating database: {err}")
        connection.rollback()
        
    finally:
        cursor.close()
        connection.close()

# Example usage (uncomment to test in your terminal if you have a tenant ID 1):
# archive_tenant(1)