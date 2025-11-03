# Job Application Tracker

A comprehensive web application for tracking job applications, built with Flask, MySQL, HTML, and CSS.

## Features

- ✅ **User Authentication**: Login and Sign Up with session management
- ✅ **Job Management**: Add, edit, and delete job applications
- ✅ **Company Management**: Manage company information
- ✅ **Recruitment Management**: Track recruiter details
- ✅ **Interview Scheduling**: Schedule and manage interviews
- ✅ **Attachment Management**: Upload and manage documents (Resume, Cover Letter, Portfolio, etc.)
- ✅ **Dashboard**: Overview of all applications with statistics
- ✅ **Profile Management**: Update user profile and contact information
- ✅ **Database Triggers**: Data validation and integrity checks

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd DBMS-PROJECT
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   
   # On Windows
   .venv\Scripts\activate
   
   # On Linux/Mac
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up MySQL database**
   - Create a MySQL database
   - Update `db_config` in `app.py` with your MySQL credentials
   - Run the SQL setup file:
   ```bash
   mysql -u root -p < database_setup.sql
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open your browser and go to: `http://localhost:5000`

## Database Structure

The application uses the following main tables:

- **Users**: Store user information and credentials
- **Company**: Company details
- **Recruitment**: Recruiter information
- **Job**: Job application details
- **Interview**: Interview scheduling
- **Interview_Process**: Links users to interviews and jobs
- **Attachments**: User documents (Resume, Cover Letter, etc.)
- **RoundsofInterview**: Interview round details
- **JobLocation**: Job location information
- **UserPhone**: User phone numbers

## Database Triggers

The application includes several triggers for data validation:

1. **DOB Validation**: Ensures date of birth is not in the future
2. **Phone Number Uniqueness**: Validates phone numbers are unique
3. **Email Uniqueness**: Validates recruitment emails are unique
4. **Interview Date Validation**: Ensures interview dates are reasonable
5. **Auto Interview ID Generation**: Automatically generates interview IDs

## Stored Procedures

1. `getApplicationCount(user_id)`: Get count of applications for a user
2. `getUserInterviewCount(user_id)`: Get count of interviews for a user
3. `assignRecruiterToJob(job_id, recruiter_id)`: Assign recruiter to a job
4. `scheduleInterview(user_id, job_id, date, mode)`: Schedule a new interview

## Usage

1. **Login**: Use your credentials or sign up for a new account
2. **Dashboard**: View all your job applications at a glance
3. **Add Jobs**: Click "Add New Job" to track new applications
4. **Manage Companies**: Add and manage company information
5. **Schedule Interviews**: Add interview details and track progress
6. **Upload Attachments**: Manage your documents (Resume, Cover Letter, etc.)
7. **Update Profile**: Edit your personal information

## Project Structure

```
DBMS-PROJECT/
├── app.py                  # Main Flask application
├── database_setup.sql      # Database setup with triggers
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── static/
│   └── style.css          # CSS styling
└── templates/
    ├── base.html          # Base template
    ├── login.html         # Login page
    ├── signup.html        # Sign up page
    ├── dashboard.html     # Dashboard
    ├── jobs.html          # Jobs management
    ├── companies.html     # Companies management
    ├── recruitment.html   # Recruitment management
    ├── interviews.html    # Interviews management
    ├── attachments.html   # Attachments management
    └── profile.html       # User profile
```

## Configuration

Update the database configuration in `app.py`:

```python
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'YourPassword',
    'database': 'job_application_tracker'
}
```

Also update the Flask secret key:

```python
app.secret_key = 'your-secret-key-change-this'
```

## Screenshots

- **Dashboard**: Overview with statistics and recent applications
- **Jobs Table**: Complete job application details
- **Interview Tracking**: Schedule and manage interviews
- **Document Management**: Upload and organize your documents

## Features Summary

| Feature | Status |
|---------|--------|
| User Authentication | ✅ Complete |
| Job CRUD Operations | ✅ Complete |
| Company Management | ✅ Complete |
| Recruiter Management | ✅ Complete |
| Interview Scheduling | ✅ Complete |
| Attachment Management | ✅ Complete |
| Profile Management | ✅ Complete |
| Database Triggers | ✅ Complete |
| Responsive Design | ✅ Complete |

## Future Enhancements

- [ ] Email notifications for interview reminders
- [ ] Export job applications to PDF/Excel
- [ ] Advanced filtering and search
- [ ] Dark mode theme
- [ ] File upload functionality for attachments
- [ ] Calendar view for interviews
- [ ] Analytics dashboard with charts

## Technologies Used

- **Backend**: Flask (Python)
- **Database**: MySQL
- **Frontend**: HTML5, CSS3
- **Styling**: Modern gradient design with responsive layout

## Author

Your Name

## License

This project is for educational purposes.


