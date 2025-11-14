📝 Job Application Tracker – Flask + MySQL

A full-stack web application designed to help users efficiently monitor and manage job applications, interviews, attachments, companies, and recruiters.
Built using Flask (Python) and MySQL, the project demonstrates relational database design, triggers, procedures, functions, joins, and authenticated CRUD operations.

📌 Project Overview

The Job Application Tracker allows users to manage every stage of the job-seeking process—from applying to jobs, scheduling interviews, tracking rounds, managing attachments, and storing recruiter/company details.

The system supports two roles:

User – Can manage only their data

Admin – Full CRUD access to all tables and dashboard statistics

This project is ideal for PES University students or any college student building a DBMS or web-database project.

🚀 Features
👤 User & Authentication

User signup + login with session-based authentication

Auto-generated UserID

Editable profile

Multi-valued phone numbers using separate UserPhone table

💼 Job Management

Add, edit, delete job entries

Track job roles, dates, statuses, links

Store job location (Street, City)

Recruiter assignment via stored procedure

Auto-create interview + round entries when a job is added

📝 Interview Management

Schedule interviews using procedure scheduleInterview

Edit interview mode, date, round status, number of rounds

View only user’s interviews (admin sees all)

Uses JOIN queries combining:

Interview

Interview_Process

Job

Users

RoundsOfInterview

📎 Attachment Management

Upload and categorize attachments (Resume, Portfolio, Cover Letter, Others)

View only own attachments unless admin

CRUD supported via controlled access

🏢 Company & Recruitment

Add/manage companies

Add/manage recruiters

Supervisor hierarchy

Recruiter-to-job assignment using procedure assignRecruiterToJob

📊 Dashboard (User/Admin)

Total job applications

Total interviews

Hired / Rejected / Offered / Withdrawn counts

Admin sees global stats

Users see personalized stats via SQL functions:

getApplicationCount()

getUserInterviewCount()

🛠️ Tech Stack
Layer	Technology
Backend	Flask (Python)
Database	MySQL
Frontend	HTML, CSS
Auth	Flask Sessions
DB Logic	SQL Functions, Procedures, Triggers
🗄️ Database Features
✔ Functions

getApplicationCount(user_id)

getUserInterviewCount(user_id)

✔ Stored Procedures

assignRecruiterToJob(job_id, recruiter_id)

scheduleInterview(user_id, job_id, date, mode)

✔ Triggers

DOB validation trigger

Auto-generate interview data

Ensure relational integrity

✔ Queries Implemented

Nested query → Used for dashboard job filtering

Join query → Used heavily in /interviews route

Aggregate query → Used in dashboard stats

📂 Project Structure
project/
│── app.py
│── templates/
│      ├── dashboard.html
│      ├── jobs.html
│      ├── interviews.html
│      ├── companies.html
│      ├── recruitment.html
│      ├── attachments.html
│      ├── profile.html
│      ├── login.html
│      ├── signup.html
│── static/
│      ├── style.css
│── database/
│      ├── schema.sql
│      ├── triggers.sql
│      ├── procedures.sql
│      ├── functions.sql
│── README.md

⚙️ Installation & Setup
1️⃣ Clone the repository
git clone https://github.com/your-username/job-application-tracker.git
cd job-application-tracker

2️⃣ Install dependencies
pip install -r requirements.txt

3️⃣ Configure MySQL connection

In app.py, update:

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'YOUR_PASSWORD',
    'database': 'job_application_tracker',
    'auth_plugin': 'mysql_native_password'
}

4️⃣ Import database SQL

Open MySQL Workbench → Run:

schema.sql

functions.sql

procedures.sql

triggers.sql

5️⃣ Run the app
python app.py


App runs at:

http://127.0.0.1:5000/

<img width="1687" height="894" alt="image" src="https://github.com/user-attachments/assets/f62fb2a8-4e0b-4460-be3b-e2fabcc88d99" />
