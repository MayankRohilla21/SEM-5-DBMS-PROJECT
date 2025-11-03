"""Test script to debug signup issue"""
import mysql.connector

# Test database connection
try:
    db = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Mayank@21',
        database='job_application_tracker',
        auth_plugin='mysql_native_password'
    )
    print("✅ Database connection successful!")
    
    cursor = db.cursor(dictionary=True)
    
    # Get current users
    cursor.execute("SELECT * FROM Users ORDER BY UserID")
    users = cursor.fetchall()
    print(f"\nCurrent users in database: {len(users)}")
    for user in users:
        print(f"  - {user['UserID']}: {user['Email']}")
    
    # Test insert
    print("\n🧪 Testing user creation...")
    
    # Get max ID
    cursor.execute("SELECT MAX(UserID) as max_id FROM Users")
    result = cursor.fetchone()
    print(f"Max ID: {result['max_id']}")
    
    if result and result['max_id']:
        max_id_num = int(result['max_id'][1:])
        new_user_id = f'U{str(max_id_num + 1).zfill(3)}'
    else:
        new_user_id = 'U001'
    
    print(f"New UserID will be: {new_user_id}")
    
    # Try to insert
    cursor.execute(
        "INSERT INTO Users (UserID, FName, LName, Email, UserPassword, DOB) VALUES (%s, %s, %s, %s, %s, %s)",
        (new_user_id, 'Test', 'User', 'test@test.com', 'password123', '2000-01-01')
    )
    db.commit()
    print(f"✅ Insert successful! New user: {new_user_id}")
    
    cursor.close()
    db.close()
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()


