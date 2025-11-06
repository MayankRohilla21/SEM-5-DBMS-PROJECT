from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import mysql.connector
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret-keys'

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Mayank@21',
    'database': 'job_application_tracker',
    'auth_plugin': 'mysql_native_password'  
}

def get_db_connection():
    """Get database connection"""
    return mysql.connector.connect(**db_config)

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# =====================================================
# AUTHENTICATION ROUTES
# =====================================================

@app.route('/')
def index():
    """Home page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE Email = %s AND UserPassword = %s", (email, password))
            user = cursor.fetchone()
            
            if user:
                session['user_id'] = user['UserID']
                session['user_name'] = user['FName']
                session['user_email'] = user['Email']
                flash("Login successful!", "success")
                cursor.close()
                db.close()
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid credentials!", "error")
                cursor.close()
                db.close()
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
            print(f"Login error: {str(e)}")
        finally:
            if 'db' in locals() and db.is_connected():
                if 'cursor' in locals():
                    cursor.close()
                db.close()
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page"""
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        password = request.form['password']
        dob = request.form.get('dob') if request.form.get('dob') else None
        
        try:
            # Client-side guard: prevent future DOB before hitting DB/trigger
            try:
                if dob:
                    dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
                    if dob_date >= datetime.now().date():
                        flash("DOB must be before today", "error")
                        return redirect(url_for('signup'))
            except Exception:
                pass

            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            
            # Check if email exists
            cursor.execute("SELECT * FROM users WHERE Email = %s", (email,))
            if cursor.fetchone():
                flash("Email already exists!", "error")
                cursor.close()
                db.close()
                return redirect(url_for('signup'))
            
            # Generate UserID - get max existing ID
            cursor.execute("SELECT MAX(UserID) as max_id FROM users")
            result = cursor.fetchone()
            if result and result['max_id']:
                max_id_num = int(result['max_id'][1:])  # Extract number part (e.g., 'U005' -> 5)
                user_id = f'U{str(max_id_num + 1).zfill(3)}'
            else:
                user_id = 'U001'
            
            # Insert user
            cursor.execute(
                "INSERT INTO users (UserID, FName, LName, Email, UserPassword, DOB) VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, fname, lname, email, password, dob)
            )
            db.commit()
            cursor.close()
            
            flash("Signup successful! Please login.", "success")
            db.close()
            return redirect(url_for('login'))
        except Exception as e:
            # If trigger message is raised, show a friendly error
            message = str(e)
            if 'DOB must be before today' in message:
                flash('DOB must be before today', 'error')
            else:
                flash(f"Error: {message}", "error")
            print(f"Signup error: {str(e)}")  # Debug print
        finally:
            if 'db' in locals() and db.is_connected():
                cursor.close()
                db.close()
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for('login'))

# =====================================================
# DASHBOARD
# =====================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard with job listings and statistics (via MySQL functions)"""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT getApplicationcount(%s) AS total_apps", (session['user_id'],))
        total_apps_result = cursor.fetchone()
        total_apps = total_apps_result['total_apps'] if total_apps_result else 0

        cursor.execute("SELECT getUserInterviewCount(%s) AS total_interviews", (session['user_id'],))
        total_interviews_result = cursor.fetchone()
        total_interviews = total_interviews_result['total_interviews'] if total_interviews_result else 0

        query = """
        SELECT 
            j.JobID,
            j.Role,
            j.Status,
            j.Dateofapplication,
            j.Link,
            j.Updation_Date,
            c.Company_Name,
            c.CompanyID,
            r.FName as RecruiterFName,
            r.LName as RecruiterLName,
            r.Email as RecruiterEmail,
            r.Phonenumber as RecruiterPhone,
            jl.Street,
            jl.City
        FROM job j
        LEFT JOIN company c ON j.CompanyID = c.CompanyID
        LEFT JOIN recruitment r ON j.RecruitmentID = r.RecruitmentID
        LEFT JOIN joblocation jl ON j.JobID = jl.JobID
        WHERE j.JobID IN (SELECT JobID FROM interview_process WHERE UserID = %s)
        ORDER BY j.Dateofapplication DESC
        """
        cursor.execute(query, (session['user_id'],))
        jobs = cursor.fetchall()

        cursor.close()
        db.close()

        return render_template(
            'dashboard.html',
            jobs=jobs,
            total_apps=total_apps,
            total_interviews=total_interviews
        )

    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "error")
        print(f"Dashboard error: {str(e)}")
        return render_template('dashboard.html', jobs=[], total_apps=0, total_interviews=0)

    finally:
        if 'db' in locals() and db.is_connected():
            if 'cursor' in locals():
                cursor.close()
            db.close()

# =====================================================
# JOBS CRUD
# =====================================================

@app.route('/jobs')
@login_required
def jobs():
    """View all jobs"""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Support sorting by JobID via ?sort=id_asc or ?sort=id_desc
        sort = request.args.get('sort', '')
        if sort == 'id_asc':
            order_clause = 'ORDER BY j.JobID ASC'
        elif sort == 'id_desc':
            order_clause = 'ORDER BY j.JobID DESC'
        else:
            order_clause = 'ORDER BY j.Dateofapplication DESC'

        query = f"""
            SELECT j.*, c.Company_Name, r.FName as RecruiterFName, r.LName as RecruiterLName,
                   jl.Street, jl.City
            FROM job j
            LEFT JOIN company c ON j.CompanyID = c.CompanyID
            LEFT JOIN recruitment r ON j.RecruitmentID = r.RecruitmentID
            LEFT JOIN joblocation jl ON j.JobID = jl.JobID
            WHERE j.JobID IN (SELECT JobID FROM interview_process WHERE UserID = %s)
            {order_clause}
        """
        cursor.execute(query, (session['user_id'],))
        jobs = cursor.fetchall()
        
        # Get companies and recruiters for dropdown
        cursor.execute("SELECT CompanyID, Company_Name FROM company")
        companies = cursor.fetchall()
        
        cursor.execute("SELECT RecruitmentID, FName, LName FROM recruitment")
        recruiters = cursor.fetchall()
        
        db.close()
        return render_template('jobs.html', jobs=jobs, companies=companies, recruiters=recruiters, sort=sort)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return render_template('jobs.html', jobs=[], companies=[], recruiters=[])

@app.route('/jobs/add', methods=['POST'])
@login_required
def add_job():
    """Add job"""
    try:
        job_id = request.form.get('job_id', '').strip()
        role = request.form.get('role', '').strip()
        status = request.form.get('status', '').strip()
        link = request.form.get('link', '').strip() or None
        company_id = request.form.get('company_id', '').strip() or None
        recruitment_id = request.form.get('recruitment_id', '').strip() or None
        street = request.form.get('street', '').strip()
        city = request.form.get('city', '').strip()
        date_applied = request.form.get('date_applied', '').strip()
        
        if not job_id or not role or not status:
            flash("Error: Job ID, Role, and Status are required", "error")
            return redirect(url_for('jobs'))
        
        # Validate status matches ENUM
        valid_statuses = ['Applied', 'Interview', 'Rejected', 'Hired', 'Offered', 'Withdrawn']
        if status not in valid_statuses:
            flash(f"Error: Invalid status. Must be one of: {', '.join(valid_statuses)}", "error")
            return redirect(url_for('jobs'))
        
        # Parse date or use today
        if date_applied:
            try:
                date_applied = datetime.strptime(date_applied, '%Y-%m-%d').date()
            except Exception:
                date_applied = datetime.now().date()
        else:
            date_applied = datetime.now().date()
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Check if job ID already exists
        cursor.execute("SELECT * FROM job WHERE JobID=%s", (job_id,))
        if cursor.fetchone():
            flash(f"Error: Job ID {job_id} already exists", "error")
            cursor.close()
            db.close()
            return redirect(url_for('jobs'))

        # Insert job
        cursor.execute("""
            INSERT INTO job (JobID, Dateofapplication, Status, Link, Role, CompanyID, RecruitmentID)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (job_id, date_applied, status, link, role, company_id, recruitment_id))
        
        # Insert job location if provided
        if street or city:
            cursor.execute("""
                INSERT INTO joblocation (JobID, Street, City) VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE Street=%s, City=%s
            """, (job_id, street or None, city or None, street or None, city or None))
        # Automatically create an Interview and Interview_Process mapping so the job
        # appears in the user's listing (the Interview table has a trigger to
        # auto-generate InterviewID if NULL, but we'll create an ID deterministically
        # to avoid race conditions).
        try:
            cursor.execute("SELECT CONCAT('I', LPAD(COALESCE(MAX(CAST(SUBSTRING(InterviewID,2) AS UNSIGNED)), 0) + 1, 3, '0')) as next_id FROM Interview")
            next_row = cursor.fetchone()
            next_interview_id = next_row['next_id'] if next_row else None
            if next_interview_id:
                # Insert Interview (ID and no date)
                cursor.execute("INSERT INTO interview (InterviewID, IDate) VALUES (%s, %s)", (next_interview_id, None))
                # Link the interview to this user and job (default Mode='Online')
                cursor.execute("INSERT INTO interview_process (UserID, InterviewID, JobID, Mode) VALUES (%s, %s, %s, %s)", (session['user_id'], next_interview_id, job_id, 'Online'))
                # Insert a default round for this interview
                cursor.execute("INSERT INTO roundsofinterview (InterviewID, Rounds, RoundStatus, Description) VALUES (%s, %s, %s, %s)", (next_interview_id, 1, 'Pending', 'Auto-created with job.'))
        except Exception as inner_e:
            # If any of these optional auto-steps fail, log but don't block job creation
            print(f"Warning: auto-create interview/process failed: {inner_e}")
        
        db.commit()
        cursor.close()
        db.close()
        flash("Job added successfully!", "success")
    except Exception as e:
        flash(f"Error adding job: {str(e)}", "error")
        print(f"Add job error: {str(e)}")
    finally:
        if 'db' in locals() and db.is_connected():
            if 'cursor' in locals():
                cursor.close()
            db.close()
    return redirect(url_for('jobs'))
@app.route('/jobs/edit/<job_id>', methods=['POST'])
@login_required
def edit_job(job_id):
    """Edit job"""
    try:
        role = request.form.get('role', '').strip()
        status = request.form.get('status', '').strip()
        link = request.form.get('link', '').strip() or None
        company_id = request.form.get('company_id', '').strip() or None
        recruitment_id = request.form.get('recruitment_id', '').strip() or None
        date_applied = request.form.get('date_applied', '').strip() or None
        street = request.form.get('street', '').strip()
        city = request.form.get('city', '').strip()

        # ✅ Basic validation
        if not role or not status:
            flash("Error: Role and Status are required", "error")
            return redirect(url_for('jobs'))

        # ✅ Validate job status
        valid_statuses = ['Applied', 'Interview', 'Rejected', 'Hired', 'Offered', 'Withdrawn']
        if status not in valid_statuses:
            flash(f"Error: Invalid status. Must be one of: {', '.join(valid_statuses)}", "error")
            return redirect(url_for('jobs'))

        # ✅ Parse date
        if date_applied:
            try:
                date_applied = datetime.strptime(date_applied, '%Y-%m-%d').date()
            except Exception:
                date_applied = None

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # ✅ Check if job exists
        cursor.execute("SELECT * FROM job WHERE JobID=%s", (job_id,))
        if not cursor.fetchone():
            flash("Error: Job not found", "error")
            cursor.close()
            db.close()
            return redirect(url_for('jobs'))

        # ✅ Update core job fields (except recruiter)
        cursor.execute("""
            UPDATE job 
            SET Role=%s, Status=%s, Link=%s, CompanyID=%s, Dateofapplication=%s
            WHERE JobID=%s
        """, (role, status, link, company_id, date_applied, job_id))

        # ✅ Call stored procedure to assign recruiter (if selected)
        if recruitment_id:
            cursor.callproc('assignRecruiterToJob', [job_id, recruitment_id])
            flash(f"Recruiter {recruitment_id} assigned successfully (via procedure).", "info")

        # ✅ Update or insert job location
        if street or city:
            cursor.execute("SELECT * FROM joblocation WHERE JobID = %s", (job_id,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE joblocation
                    SET Street = %s, City = %s
                    WHERE JobID = %s
                """, (street, city, job_id))
            else:
                cursor.execute("""
                    INSERT INTO joblocation (JobID, Street, City)
                    VALUES (%s, %s, %s)
                """, (job_id, street or None, city or None))
        else:
            cursor.execute("DELETE FROM joblocation WHERE JobID=%s", (job_id,))

        db.commit()
        flash("Job updated successfully!", "success")

    except Exception as e:
        if 'db' in locals():
            db.rollback()
        flash(f"Error updating job: {str(e)}", "error")
        print(f"Edit job error: {str(e)}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.is_connected():
            db.close()

    return redirect(url_for('jobs'))

@app.route('/jobs/delete/<job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    """Delete job"""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("DELETE FROM job WHERE JobID=%s", (job_id,))
        db.commit()
        cursor.close()
        db.close()
        flash("Job deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting job: {str(e)}", "error")
        print(f"Delete job error: {str(e)}")
    finally:
        if 'db' in locals() and db.is_connected():
            if 'cursor' in locals():
                cursor.close()
            db.close()
    return redirect(url_for('jobs'))

# =====================================================
# COMPANIES CRUD
# =====================================================

@app.route('/companies')
@login_required
def companies():
    """View all companies"""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        # Support sorting by CompanyID via ?sort=id_asc or ?sort=id_desc
        sort = request.args.get('sort', '')
        if sort == 'id_asc':
            order_clause = 'ORDER BY CompanyID ASC'
        elif sort == 'id_desc':
            order_clause = 'ORDER BY CompanyID DESC'
        else:
            order_clause = 'ORDER BY Company_Name'

        cursor.execute(f"SELECT * FROM company {order_clause}")
        companies = cursor.fetchall()
        db.close()
        return render_template('companies.html', companies=companies, sort=sort)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return render_template('companies.html', companies=[])

@app.route('/companies/add', methods=['POST'])
@login_required
def add_company():
    """Add company"""
    try:
        company_id = request.form.get('company_id', '').strip()
        name = request.form.get('name', '').strip()
        website = request.form.get('website', '').strip()
        
        if not company_id or not name or not website:
            flash("Error: Company ID, Name, and Website are required", "error")
            return redirect(url_for('companies'))
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Check if company ID already exists
        cursor.execute("SELECT * FROM company WHERE CompanyID=%s", (company_id,))
        if cursor.fetchone():
            flash(f"Error: Company ID {company_id} already exists", "error")
            cursor.close()
            db.close()
            return redirect(url_for('companies'))
        
        cursor.execute("INSERT INTO company (CompanyID, Company_Name, Website) VALUES (%s, %s, %s)",
                      (company_id, name, website))
        db.commit()
        cursor.close()
        db.close()
        flash("Company added successfully!", "success")
    except Exception as e:
        flash(f"Error adding company: {str(e)}", "error")
        print(f"Add company error: {str(e)}")
    finally:
        if 'db' in locals() and db.is_connected():
            if 'cursor' in locals():
                cursor.close()
            db.close()
    return redirect(url_for('companies'))

@app.route('/companies/edit/<company_id>', methods=['POST'])
@login_required
def edit_company(company_id):
    """Edit company"""
    try:
        name = request.form.get('name', '').strip()
        website = request.form.get('website', '').strip()
        
        if not name or not website:
            flash("Error: Company Name and Website are required", "error")
            return redirect(url_for('companies'))
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Check if company exists
        cursor.execute("SELECT * FROM company WHERE CompanyID=%s", (company_id,))
        if not cursor.fetchone():
            flash(f"Error: Company not found", "error")
            cursor.close()
            db.close()
            return redirect(url_for('companies'))
        
        cursor.execute("UPDATE company SET Company_Name=%s, Website=%s WHERE CompanyID=%s",
                      (name, website, company_id))
        db.commit()
        cursor.close()
        db.close()
        flash("Company updated successfully!", "success")
    except Exception as e:
        flash(f"Error updating company: {str(e)}", "error")
        print(f"Edit company error: {str(e)}")
    finally:
        if 'db' in locals() and db.is_connected():
            if 'cursor' in locals():
                cursor.close()
            db.close()
    return redirect(url_for('companies'))

@app.route('/companies/delete/<company_id>', methods=['POST'])
@login_required
def delete_company(company_id):
    """Delete company"""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("DELETE FROM company WHERE CompanyID=%s", (company_id,))
        db.commit()
        cursor.close()
        db.close()
        flash("Company deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting company: {str(e)}", "error")
        print(f"Delete company error: {str(e)}")
    finally:
        if 'db' in locals() and db.is_connected():
            if 'cursor' in locals():
                cursor.close()
            db.close()
    return redirect(url_for('companies'))

# =====================================================
# RECRUITMENT CRUD
# =====================================================

@app.route('/recruitment')
@login_required
def recruitment():
    """View all recruiters"""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        # Support sorting by RecruitmentID via ?sort=id_asc or ?sort=id_desc
        sort = request.args.get('sort', '')
        if sort == 'id_asc':
            order_clause = 'ORDER BY r.RecruitmentID ASC'
        elif sort == 'id_desc':
            order_clause = 'ORDER BY r.RecruitmentID DESC'
        else:
            order_clause = ''

        cursor.execute(f"""
            SELECT r.*, c.Company_Name, s.FName as SupervisorFName, s.LName as SupervisorLName
            FROM recruitment r
            LEFT JOIN company c ON r.CompanyID = c.CompanyID
            LEFT JOIN recruitment s ON r.SUPERVISOR = s.RecruitmentID
            {order_clause}
        """)
        recruiters = cursor.fetchall()

        cursor.execute("SELECT RecruitmentID FROM recruitment")
        all_recruiters = cursor.fetchall()

        cursor.execute("SELECT CompanyID, Company_Name FROM company")
        companies = cursor.fetchall()

        db.close()
        return render_template('recruitment.html', recruiters=recruiters, companies=companies, all_recruiters=all_recruiters, sort=sort)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return render_template('recruitment.html', recruiters=[], companies=[], all_recruiters=[])

@app.route('/recruitment/add', methods=['POST'])
@login_required
def add_recruiter():
    """Add recruiter"""
    try:
        recruiter_id = request.form.get('recruiter_id', '').strip()
        fname = request.form.get('fname', '').strip()
        lname = request.form.get('lname', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        company_id = request.form.get('company_id', '').strip() or None
        supervisor = request.form.get('supervisor', '').strip() or None
        
        if not recruiter_id or not fname or not lname or not phone or not email:
            flash("Error: Recruiter ID, First Name, Last Name, Phone, and Email are required", "error")
            return redirect(url_for('recruitment'))
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Check if recruiter ID already exists
        cursor.execute("SELECT * FROM recruitment WHERE RecruitmentID=%s", (recruiter_id,))
        if cursor.fetchone():
            flash(f"Error: Recruiter ID {recruiter_id} already exists", "error")
            cursor.close()
            db.close()
            return redirect(url_for('recruitment'))
        
        cursor.execute("""
            INSERT INTO recruitment (RecruitmentID, FName, LName, Phonenumber, Email, CompanyID, SUPERVISOR)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (recruiter_id, fname, lname, phone, email, company_id, supervisor))
        db.commit()
        cursor.close()
        db.close()
        flash("Recruiter added successfully!", "success")
    except Exception as e:
        flash(f"Error adding recruiter: {str(e)}", "error")
        print(f"Add recruiter error: {str(e)}")
    finally:
        if 'db' in locals() and db.is_connected():
            if 'cursor' in locals():
                cursor.close()
            db.close()
    return redirect(url_for('recruitment'))

@app.route('/recruitment/edit/<recruiter_id>', methods=['POST'])
@login_required
def edit_recruiter(recruiter_id):
    """Edit recruiter"""
    try:
        fname = request.form.get('fname', '').strip()
        lname = request.form.get('lname', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        company_id = request.form.get('company_id', '').strip() or None
        supervisor = request.form.get('supervisor', '').strip() or None
        
        if not fname or not lname or not phone or not email:
            flash("Error: First Name, Last Name, Phone, and Email are required", "error")
            return redirect(url_for('recruitment'))
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Check if recruiter exists
        cursor.execute("SELECT * FROM recruitment WHERE RecruitmentID=%s", (recruiter_id,))
        if not cursor.fetchone():
            flash(f"Error: Recruiter not found", "error")
            cursor.close()
            db.close()
            return redirect(url_for('recruitment'))
        
        cursor.execute("""
            UPDATE recruitment 
            SET FName=%s, LName=%s, Phonenumber=%s, Email=%s, CompanyID=%s, SUPERVISOR=%s
            WHERE RecruitmentID=%s
        """, (fname, lname, phone, email, company_id, supervisor, recruiter_id))
        db.commit()
        cursor.close()
        db.close()
        flash("Recruiter updated successfully!", "success")
    except Exception as e:
        flash(f"Error updating recruiter: {str(e)}", "error")
        print(f"Edit recruiter error: {str(e)}")
    finally:
        if 'db' in locals() and db.is_connected():
            if 'cursor' in locals():
                cursor.close()
            db.close()
    return redirect(url_for('recruitment'))

@app.route('/recruitment/delete/<recruiter_id>', methods=['POST'])
@login_required
def delete_recruiter(recruiter_id):
    """Delete recruiter"""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("DELETE FROM recruitment WHERE RecruitmentID=%s", (recruiter_id,))
        db.commit()
        cursor.close()
        db.close()
        flash("Recruiter deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting recruiter: {str(e)}", "error")
        print(f"Delete recruiter error: {str(e)}")
    finally:
        if 'db' in locals() and db.is_connected():
            if 'cursor' in locals():
                cursor.close()
            db.close()
    return redirect(url_for('recruitment'))

# =====================================================
# INTERVIEWS CRUD
# =====================================================

@app.route('/interviews')
@login_required
def interviews():
    """View all interviews"""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Support sorting by InterviewID via ?sort=id_asc or ?sort=id_desc
        sort = request.args.get('sort', '')
        if sort == 'id_asc':
            order_clause = 'ORDER BY COALESCE(ip.InterviewID, i.InterviewID) ASC'
        elif sort == 'id_desc':
            order_clause = 'ORDER BY COALESCE(ip.InterviewID, i.InterviewID) DESC'
        else:
            order_clause = 'ORDER BY i.IDate IS NULL, i.IDate DESC, COALESCE(ip.InterviewID, i.InterviewID) DESC'

        query = f"""
            SELECT 
                COALESCE(ip.InterviewID, i.InterviewID) AS InterviewID,
                ip.UserID,
                ip.JobID,
                ip.Mode,
                i.IDate,
                j.Role,
                u.FName,
                u.LName,
                COALESCE(r.RoundStatus, 'Pending') as RoundStatus,
                r.Description,
                r.Rounds
            FROM interview i
            LEFT JOIN interview_process ip ON i.InterviewID = ip.InterviewID
            LEFT JOIN job j ON ip.JobID = j.JobID
            LEFT JOIN users u ON ip.UserID = u.UserID
            LEFT JOIN roundsofinterview r ON i.InterviewID = r.InterviewID
            WHERE ip.UserID = %s
            {order_clause}
        """
        cursor.execute(query, (session['user_id'],))
        interviews = cursor.fetchall()

        # Debug: Print the count and first few records
        print(f"Found {len(interviews)} interviews")
        if interviews:
            print(f"Sample interview: {interviews[0]}")

        cursor.execute("SELECT JobID, Role FROM job")
        jobs = cursor.fetchall()

        # Only show the logged-in user in the users dropdown (don't expose others)
        cursor.execute("SELECT UserID, FName, LName FROM users WHERE UserID=%s", (session['user_id'],))
        users = cursor.fetchall()

        db.close()
        return render_template('interviews.html', interviews=interviews, jobs=jobs, users=users, sort=sort)
    except Exception as e:
        flash(f"Error loading interviews: {str(e)}", "error")
        print(f"Interviews error: {str(e)}")  # Debug print
        return render_template('interviews.html', interviews=[], jobs=[], users=[])
    finally:
        if 'db' in locals() and db.is_connected():
            if 'cursor' in locals():
                cursor.close()
            db.close()

@app.route('/interviews/add', methods=['POST'])
@login_required
def add_interview():
    """Add interview (via stored procedure)"""
    try:
        user_id = request.form.get('user_id', '').strip()
        job_id = request.form.get('job_id', '').strip()
        mode = request.form.get('mode', '').strip()
        date = request.form.get('date', '').strip()

        if not user_id or not job_id or not mode or not date:
            flash("Error: User, Job, Mode, and Date are required", "error")
            return redirect(url_for('interviews'))

        valid_modes = ['Online', 'Offline']
        if mode not in valid_modes:
            flash(f"Error: Invalid mode. Must be one of: {', '.join(valid_modes)}", "error")
            return redirect(url_for('interviews'))

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.callproc('scheduleInterview', [user_id, job_id, date, mode])

        db.commit()
        cursor.close()
        db.close()

        flash("Interview scheduled successfully using stored procedure!", "success")

    except Exception as e:
        flash(f"Error adding interview: {str(e)}", "error")
        print(f"Add interview (procedure) error: {str(e)}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db.is_connected():
            db.close()

    return redirect(url_for('interviews'))

@app.route('/interviews/edit/<interview_id>', methods=['POST'])
@login_required
def edit_interview(interview_id):
    """Edit interview"""
    try:
        date = request.form.get('date', '').strip()
        mode = request.form.get('mode', '').strip()
        round_status = request.form.get('round_status', '').strip()
        rounds = request.form.get('rounds', '').strip()
        description = request.form.get('description', '').strip()
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
    # Check if interview exists
        cursor.execute("SELECT * FROM interview WHERE InterviewID=%s", (interview_id,))
        if not cursor.fetchone():
            flash(f"Error: Interview not found", "error")
            cursor.close()
            db.close()
            return redirect(url_for('interviews'))
        
        # Validate mode if provided
        if mode:
            valid_modes = ['Online', 'Offline']
            if mode not in valid_modes:
                flash(f"Error: Invalid mode. Must be one of: {', '.join(valid_modes)}", "error")
                cursor.close()
                db.close()
                return redirect(url_for('interviews'))
        
        # Validate RoundStatus if provided
        if round_status:
            valid_statuses = ['Pending', 'Completed', 'In Progress', 'Cancelled']
            if round_status not in valid_statuses:
                flash(f"Error: Invalid round status. Must be one of: {', '.join(valid_statuses)}", "error")
                cursor.close()
                db.close()
                return redirect(url_for('interviews'))
        
        # Validate and parse rounds
        try:
            rounds_int = int(rounds) if rounds else None
            if rounds_int and rounds_int < 1:
                rounds_int = 1
        except (ValueError, TypeError):
            rounds_int = None
        
        # Update Interview table (date)
        if date:
            cursor.execute("""
                UPDATE interview 
                SET IDate = %s
                WHERE InterviewID = %s
            """, (date, interview_id))
        
        # Update Interview_Process table (mode)
        if mode:
            cursor.execute("""
                UPDATE interview_process 
                SET Mode = %s
                WHERE InterviewID = %s
            """, (mode, interview_id))
        
        # Update RoundsofInterview table (rounds, status, description)
        # First check if record exists
        cursor.execute("SELECT * FROM roundsofinterview WHERE InterviewID = %s", (interview_id,))
        round_exists = cursor.fetchone()
        
        if round_exists:
            # Update existing round - use existing values if not provided
            update_rounds = rounds_int if rounds_int else round_exists['Rounds']
            update_status = round_status if round_status else round_exists['RoundStatus']
            update_description = description if description else round_exists.get('Description', '')
            
            cursor.execute("""
                UPDATE roundsofinterview 
                SET Rounds = %s, RoundStatus = %s, Description = %s
                WHERE InterviewID = %s
            """, (update_rounds, update_status, update_description, interview_id))
        else:
            # Insert new round if it doesn't exist
            insert_rounds = rounds_int if rounds_int else 1
            insert_status = round_status if round_status else 'Pending'
            cursor.execute("""
                INSERT INTO roundsofinterview (InterviewID, Rounds, RoundStatus, Description)
                VALUES (%s, %s, %s, %s)
            """, (interview_id, insert_rounds, insert_status, description or 'Initial round scheduled.'))
        
        db.commit()
        cursor.close()
        db.close()
        flash("Interview updated successfully!", "success")
    except Exception as e:
        flash(f"Error updating interview: {str(e)}", "error")
        print(f"Edit interview error: {str(e)}")
    finally:
        if 'db' in locals() and db.is_connected():
            if 'cursor' in locals():
                cursor.close()
            db.close()
    return redirect(url_for('interviews'))

@app.route('/interviews/delete/<interview_id>', methods=['POST'])
@login_required
def delete_interview(interview_id):
    """Delete interview"""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        # Note: Due to CASCADE DELETE, deleting from interview will automatically
        # delete related records in interview_process and roundsofinterview
        cursor.execute("DELETE FROM interview WHERE InterviewID=%s", (interview_id,))
        db.commit()
        cursor.close()
        db.close()
        flash("Interview deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting interview: {str(e)}", "error")
        print(f"Delete interview error: {str(e)}")
    finally:
        if 'db' in locals() and db.is_connected():
            if 'cursor' in locals():
                cursor.close()
            db.close()
    return redirect(url_for('interviews'))

# =====================================================
# ATTACHMENTS CRUD
# =====================================================

@app.route('/attachments')
@login_required
def attachments():
    """View all attachments"""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        # Support sorting by AttachmentID via ?sort=id_asc or ?sort=id_desc
        sort = request.args.get('sort', '')
        if sort == 'id_asc':
            order_clause = 'ORDER BY a.AttachmentID ASC'
        elif sort == 'id_desc':
            order_clause = 'ORDER BY a.AttachmentID DESC'
        else:
            order_clause = 'ORDER BY a.Type, a.AttachmentID'

        # Show only attachments belonging to the logged-in user
        query = f"""
            SELECT a.*, u.FName, u.LName
            FROM attachments a
            LEFT JOIN users u ON a.UserID = u.UserID
            WHERE a.UserID = %s
            {order_clause}
        """
        cursor.execute(query, (session['user_id'],))
        attachments = cursor.fetchall()
        
        # Debug: Print the count and first few records
        print(f"Found {len(attachments)} attachments")
        if attachments:
            print(f"Sample attachment: {attachments[0]}")
        
        db.close()
        return render_template('attachments.html', attachments=attachments, sort=sort)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return render_template('attachments.html', attachments=[])

@app.route('/attachments/add', methods=['POST'])
@login_required
def add_attachment():
    """Add attachment"""
    try:
        attachment_id = request.form.get('attachment_id', '').strip()
        file_url = request.form.get('file_url', '').strip()
        file_name = request.form.get('file_name', '').strip()
        file_type = request.form.get('file_type', '').strip()
        
        # Validate file_type matches ENUM values exactly (case-sensitive)
        valid_types = ['Resume', 'Cover Letter', 'Portfolio', 'Others']
        if file_type not in valid_types:
            flash(f"Error: Invalid file type. Must be one of: {', '.join(valid_types)}", "error")
            return redirect(url_for('attachments'))
        
        if not attachment_id or not file_name or not file_type:
            flash("Error: Attachment ID, File Name, and Type are required", "error")
            return redirect(url_for('attachments'))
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
    # Check if attachment ID already exists
        cursor.execute("SELECT * FROM attachments WHERE AttachmentID=%s", (attachment_id,))
        if cursor.fetchone():
            flash(f"Error: Attachment ID {attachment_id} already exists", "error")
            cursor.close()
            db.close()
            return redirect(url_for('attachments'))
        
        cursor.execute("""
            INSERT INTO attachments (AttachmentID, File_url, File_Name, Type, UserID)
            VALUES (%s, %s, %s, %s, %s)
        """, (attachment_id, file_url, file_name, file_type, session['user_id']))
        db.commit()
        cursor.close()
        db.close()
        flash("Attachment added successfully!", "success")
    except Exception as e:
        flash(f"Error adding attachment: {str(e)}", "error")
        print(f"Add attachment error: {str(e)}")
    return redirect(url_for('attachments'))

@app.route('/attachments/edit/<attachment_id>', methods=['POST'])
@login_required
def edit_attachment(attachment_id):
    """Edit attachment"""
    try:
        file_url = request.form.get('file_url', '').strip()
        file_name = request.form.get('file_name', '').strip()
        file_type = request.form.get('file_type', '').strip()
        
        # Debug: Print received values
        print(f"Edit attachment - ID: {attachment_id}, Name: {file_name}, Type: {file_type}, URL: {file_url}")
        
        # Validate file_type matches ENUM values
        valid_types = ['Resume', 'Cover Letter', 'Portfolio', 'Others']
        if file_type not in valid_types:
            flash(f"Error: Invalid file type. Must be one of: {', '.join(valid_types)}", "error")
            return redirect(url_for('attachments'))
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
    # Check if attachment exists
        cursor.execute("SELECT * FROM attachments WHERE AttachmentID=%s", (attachment_id,))
        attachment = cursor.fetchone()

        if not attachment:
            flash(f"Error: Attachment not found", "error")
            db.close()
            return redirect(url_for('attachments'))

        # Restrict editing to owner
        if attachment.get('UserID') != session['user_id']:
            flash("Error: You are not authorized to edit this attachment", "error")
            db.close()
            return redirect(url_for('attachments'))
        cursor.execute("""
            UPDATE attachments 
            SET File_url=%s, File_Name=%s, Type=%s
            WHERE AttachmentID=%s
        """, (file_url, file_name, file_type, attachment_id))
        
        # Verify the update
        cursor.execute("SELECT Type FROM attachments WHERE AttachmentID=%s", (attachment_id,))
        updated = cursor.fetchone()
        print(f"After update - Type in DB: {updated['Type'] if updated else 'NOT FOUND'}")
        
        db.commit()
        cursor.close()
        db.close()
        flash("Attachment updated successfully!", "success")
    except Exception as e:
        flash(f"Error updating attachment: {str(e)}", "error")
        print(f"Edit attachment error: {str(e)}")  # Debug print
    return redirect(url_for('attachments'))

@app.route('/attachments/delete/<attachment_id>', methods=['POST'])
@login_required
def delete_attachment(attachment_id):
    """Delete attachment"""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        # Remove UserID restriction since we show all attachments
        # Verify ownership before deleting
        cursor.execute("SELECT UserID FROM attachments WHERE AttachmentID=%s", (attachment_id,))
        att = cursor.fetchone()
        if not att:
            flash("Error: Attachment not found", "error")
            cursor.close()
            db.close()
            return redirect(url_for('attachments'))
        if att.get('UserID') != session['user_id']:
            flash("Error: You are not authorized to delete this attachment", "error")
            cursor.close()
            db.close()
            return redirect(url_for('attachments'))

        cursor.execute("DELETE FROM attachments WHERE AttachmentID=%s", (attachment_id,))
        db.commit()
        cursor.close()
        db.close()
        flash("Attachment deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting attachment: {str(e)}", "error")
        print(f"Delete attachment error: {str(e)}")
    return redirect(url_for('attachments'))

# =====================================================
# USER PROFILE
# =====================================================

@app.route('/profile')
@login_required
def profile():
    """View user profile"""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE UserID=%s", (session['user_id'],))
        user = cursor.fetchone()
        
        cursor.execute("SELECT PhoneNo FROM userphone WHERE UserID=%s", (session['user_id'],))
        phones = cursor.fetchall()
        
        db.close()
        return render_template('profile.html', user=user, phones=phones)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('dashboard'))

@app.route('/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    try:
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        dob = request.form.get('dob')
        phone = request.form.get('phone')
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            UPDATE users SET FName=%s, LName=%s, Email=%s, DOB=%s WHERE UserID=%s
        """, (fname, lname, email, dob, session['user_id']))
        
        if phone:
            cursor.execute("DELETE FROM userphone WHERE UserID=%s", (session['user_id'],))
            cursor.execute("INSERT INTO userphone (UserID, PhoneNo) VALUES (%s, %s)",
                          (session['user_id'], phone))
        
        db.commit()
        db.close()
        flash("Profile updated successfully!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(debug=True)

