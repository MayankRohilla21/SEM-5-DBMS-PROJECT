# Quick Setup Guide

## Prerequisites

1. Python 3.7 or higher
2. MySQL Server
3. pip package manager

## Step-by-Step Setup

### 1. Database Setup

```sql
-- Login to MySQL
mysql -u root -p

-- Create and setup database
source database_setup.sql
```

Or run the SQL file manually:
```bash
mysql -u root -p < database_setup.sql
```

### 2. Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 3. Configure Database Connection

Edit `app.py` and update these lines:

```python
db_config = {
    'host': 'localhost',
    'user': 'root',              # Change if different
    'password': 'Mayank@21',      # Change to your MySQL password
    'database': 'job_application_tracker'
}
```

### 4. Update Secret Key

In `app.py`, change:
```python
app.secret_key = 'your-secret-key-change-this-to-something-random'
```

### 5. Run the Application

```bash
python app.py
```

### 6. Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

## First Login

1. Click "Sign Up" to create an account
2. Fill in your details (Date of Birth should not be in the future)
3. Login with your credentials
4. You're ready to track your job applications!

## Testing the Application

### Test Login:
- Email: `alice@example.com`
- Password: `password123`

### Try Creating:
1. A new job application
2. Add a company
3. Add a recruiter
4. Schedule an interview
5. Upload an attachment

## Features to Test

### Database Triggers

1. **DOB Validation**
   - Try signing up with a future date of birth
   - Should get an error

2. **Phone Uniqueness**
   - Add a phone number that already exists
   - Should get an error

### CRUD Operations

1. **Jobs**: Add, Edit, Delete jobs
2. **Companies**: Manage company information
3. **Recruiters**: Add recruiter details
4. **Interviews**: Schedule and track interviews
5. **Attachments**: Upload and manage documents

## Troubleshooting

### Error: Can't connect to MySQL
- Check if MySQL is running
- Verify credentials in `app.py`
- Ensure the database exists

### Error: Module not found
- Activate virtual environment
- Run `pip install -r requirements.txt`

### Error: Table doesn't exist
- Run the database setup SQL file
- Check if all tables were created

### CSS not loading
- Check if `static/style.css` exists
- Clear browser cache
- Check browser console for errors

## Next Steps

1. Explore all the features
2. Add your own job applications
3. Schedule interviews
4. Upload your documents

Enjoy tracking your job applications!

