# Fix MySQL Authentication Plugin Error

## Error Message
```
Authentication plugin 'caching_sha2_password' is not supported
```

## Solution 1: Add auth_plugin to connection (Already implemented)
I've already added this to your `app.py`:
```python
'auth_plugin': 'mysql_native_password'
```

**If this doesn't work, try the solutions below:**

## Solution 2: Change MySQL User Password Method

Run these commands in MySQL to change the authentication method for your root user:

```sql
-- Login to MySQL
mysql -u root -p

-- Change the authentication method
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'Mayank@21';

-- Or if you want to use the same password:
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'Mayank@21';

-- Flush privileges
FLUSH PRIVILEGES;
```

## Solution 3: Update mysql-connector-python

Uninstall and reinstall the connector:

```bash
pip uninstall mysql-connector-python
pip install mysql-connector-python==8.0.33
```

Then remove the `auth_plugin` line from app.py.

## Solution 4: Use PyMySQL (Alternative)

If all else fails, switch to PyMySQL which works better with newer MySQL:

### Step 1: Update requirements.txt
```
Flask==3.0.0
PyMySQL==1.1.0
```

### Step 2: Update app.py imports
```python
import pymysql
import pymysql.cursors

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Mayank@21',
    'database': 'job_application_tracker',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**db_config)
```

### Step 3: Update cursor calls
Replace `cursor(dictionary=True)` with just `cursor()` in all places.

## Quick Fix Summary

1. **First try**: Run Solution 2 (change MySQL user authentication)
2. **If that doesn't work**: Try Solution 3 (downgrade mysql-connector-python)
3. **Last resort**: Use Solution 4 (switch to PyMySQL)

## Test Connection

To test if your connection works:

```python
import mysql.connector

try:
    db = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Mayank@21',
        database='job_application_tracker',
        auth_plugin='mysql_native_password'
    )
    print("✅ Connection successful!")
    db.close()
except Exception as e:
    print(f"❌ Error: {e}")
```

## Current Status

✅ Already fixed in `app.py` with:
```python
'auth_plugin': 'mysql_native_password'
```

**Try running the app now. If it still doesn't work, use Solution 2 above.**

