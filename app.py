import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, auth
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Initialize Firebase
firebase_config = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
    "universe_domain": "googleapis.com"
}

cred = credentials.Certificate(firebase_config)
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Role required decorator
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            user_ref = db.collection('users').document(email)
            user = user_ref.get()
            
            if user.exists:
                user_data = user.to_dict()
                if user_data['password'] == password:
                    # Set all required session variables
                    session['email'] = email
                    session['name'] = user_data['name']
                    session['role'] = user_data['role']
                    session['department'] = user_data.get('department', '')
                    
                    # Set section/year based on role
                    if user_data['role'] == 'student':
                        session['section'] = user_data['section']
                        session['year'] = user_data['year']
                    elif user_data['role'] == 'faculty':
                        session['sections'] = user_data.get('sections', [])
                    
                    return redirect(url_for('dashboard'))
                else:
                    error = 'Invalid password'
            else:
                error = 'User not found'
        except Exception as e:
            error = f'Error: {str(e)}'
        
        return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        department = request.form['department']
        year = request.form['year']
        section = request.form['section']
        
        try:
            user_ref = db.collection('users').document(email)
            if user_ref.get().exists:
                error = 'Email already registered'
                return render_template('register.html', error=error)
            
            user_data = {
                'name': name,
                'email': email,
                'password': password,
                'department': department,
                'year': year,
                'section': section,
                'role': 'student',
                'created_at': firestore.SERVER_TIMESTAMP
            }
            
            user_ref.set(user_data)
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        
        except Exception as e:
            error = f'Error: {str(e)}'
            return render_template('register.html', error=error)
    
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    role = session['role']
    if role == 'student':
        return redirect(url_for('student_dashboard'))
    elif role == 'faculty':
        return redirect(url_for('faculty_dashboard'))
    elif role == 'hod':
        return redirect(url_for('hod_dashboard'))
    elif role == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('logout'))

@app.route('/student/dashboard')
@login_required
@role_required(['student'])
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/faculty/dashboard')
@login_required
@role_required(['faculty'])
def faculty_dashboard():
    forms = []
    if 'sections' in session:
        for section in session['sections']:
            section_forms = db.collection('forms').where('student_section', '==', section).where('status', '==', 'pending').stream()
            for form in section_forms:
                form_data = form.to_dict()
                form_data['id'] = form.id
                forms.append(form_data)
    
    return render_template('faculty_dashboard.html', forms=forms)

@app.route('/hod/dashboard')
@login_required
@role_required(['hod'])
def hod_dashboard():
    forms = []
    if 'department' in session:
        forms_ref = db.collection('forms').where('student_department', '==', session['department']).where('status', '==', 'pending_hod').stream()
        for form in forms_ref:
            form_data = form.to_dict()
            form_data['id'] = form.id
            forms.append(form_data)
    
    return render_template('hod_dashboard.html', forms=forms)

@app.route('/admin/dashboard')
@login_required
@role_required(['admin'])
def admin_dashboard():
    users_ref = db.collection('users').stream()
    users = []
    for user in users_ref:
        user_data = user.to_dict()
        user_data['id'] = user.id
        users.append(user_data)
    
    return render_template('admin_dashboard.html', users=users)

@app.route('/submit_form/<form_type>', methods=['GET', 'POST'])
@login_required
@role_required(['student'])
def submit_form(form_type):
    if request.method == 'POST':
        form_data = {
            'form_type': form_type,
            'student_name': session['name'],
            'student_email': session['email'],
            'student_section': session.get('section', ''),
            'student_department': session.get('department', ''),
            'student_year': session.get('year', ''),
            'reason': request.form['reason'],
            'status': 'pending',
            'hod_status': 'not_required',
            'timestamp': firestore.SERVER_TIMESTAMP,
            'approved_by': [],
            'approver_emails': []
        }
        
        if form_type == 'od':
            form_data.update({
                'date': request.form['date'],
                'start_time': request.form['start_time'],
                'end_time': request.form['end_time'],
                'duration': request.form['duration'],
                'approver_emails': request.form.getlist('faculty')
            })
        elif form_type == 'leave':
            form_data.update({
                'start_date': request.form['start_date'],
                'end_date': request.form['end_date'],
                'days': request.form['days']
            })
        elif form_type == 'gate':
            form_data.update({
                'date': request.form['date'],
                'out_time': request.form['out_time'],
                'duration': request.form['duration']
            })
        
        db.collection('forms').add(form_data)
        flash('Form submitted successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # Get faculty for the student's department and section
    faculty = []
    if 'department' in session and 'section' in session:
        faculty_ref = db.collection('users').where('role', '==', 'faculty')\
                      .where('department', '==', session['department'])\
                      .where('sections', 'array_contains', session['section'])\
                      .stream()
        for fac in faculty_ref:
            faculty_data = fac.to_dict()
            faculty_data['id'] = fac.id
            faculty.append(faculty_data)
    
    return render_template('submit_form.html', form_type=form_type, faculty=faculty)

@app.route('/approve/<form_id>')
@login_required
@role_required(['faculty'])
def approve(form_id):
    form_ref = db.collection('forms').document(form_id)
    form = form_ref.get().to_dict()
    
    if session['email'] in form['approver_emails'] and session['email'] not in form.get('approved_by', []):
        approved_by = form.get('approved_by', [])
        approved_by.append(session['name'])
        
        form_ref.update({
            'approved_by': approved_by
        })
        
        if len(approved_by) == len(form['approver_emails']):
            form_ref.update({
                'status': 'approved',
                'approved_at': firestore.SERVER_TIMESTAMP
            })
        
        flash('Form approved successfully!', 'success')
    else:
        flash('You have already approved this form or are not authorized', 'warning')
    
    return redirect(url_for('faculty_dashboard'))

@app.route('/hod_approve/<form_id>')
@login_required
@role_required(['hod'])
def hod_approve(form_id):
    form_ref = db.collection('forms').document(form_id)
    form_ref.update({
        'status': 'approved',
        'hod_status': 'approved',
        'approved_at': firestore.SERVER_TIMESTAMP
    })
    flash('Form approved by HOD!', 'success')
    return redirect(url_for('hod_dashboard'))

@app.route('/approved_forms')
@login_required
def approved_forms():
    forms = []
    
    if session['role'] == 'student':
        forms_ref = db.collection('forms').where('student_email', '==', session['email']).where('status', '==', 'approved').stream()
    elif session['role'] == 'faculty':
        forms_ref = db.collection('forms').where('student_section', 'in', session.get('sections', [])).where('status', '==', 'approved').stream()
    elif session['role'] == 'hod':
        forms_ref = db.collection('forms').where('student_department', '==', session.get('department', '')).where('status', '==', 'approved').stream()
    else:
        forms_ref = db.collection('forms').where('status', '==', 'approved').stream()
    
    for form in forms_ref:
        form_data = form.to_dict()
        form_data['id'] = form.id
        forms.append(form_data)
    
    return render_template('approved_forms.html', forms=forms)

@app.route('/admin/edit_user/<email>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_edit_user(email):
    user_ref = db.collection('users').document(email)
    user = user_ref.get().to_dict()
    
    if request.method == 'POST':
        role = request.form['role']
        department = request.form['department']
        sections = request.form.getlist('sections')
        coordinator_section = request.form.get('coordinator_section', '')
        
        update_data = {
            'role': role,
            'department': department
        }
        
        if role == 'faculty':
            update_data['sections'] = sections
            if coordinator_section:
                update_data['coordinator_section'] = coordinator_section
        elif role == 'student':
            update_data['year'] = request.form['year']
            update_data['section'] = request.form['section']
        
        user_ref.update(update_data)
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    all_sections = [f"{year}{section}" for year in range(1, 5) for section in ['A', 'B', 'C']]
    
    return render_template('admin_edit_user.html', user=user, all_sections=all_sections)

@app.route('/admin/search_users')
@login_required
@role_required(['admin'])
def admin_search_users():
    search_query = request.args.get('q', '')
    users_ref = db.collection('users')
    
    if search_query:
        users = []
        for user in users_ref.stream():
            user_data = user.to_dict()
            if search_query.lower() in user_data['email'].lower() or search_query.lower() in user_data['name'].lower():
                user_data['id'] = user.id
                users.append(user_data)
    else:
        users = [user.to_dict() for user in users_ref.stream()]
    
    return render_template('admin_dashboard.html', users=users)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)