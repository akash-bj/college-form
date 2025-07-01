import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, auth
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from datetime import datetime, time
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
                    session['email'] = email
                    session['name'] = user_data['name']
                    session['role'] = user_data['role']
                    session['department'] = user_data.get('department', '')
                    
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
    approved_count = 0
    
    if 'sections' in session:
        # Get pending forms
        for section in session['sections']:
            section_forms = db.collection('forms')\
                .where('student_section', '==', section)\
                .where('status', '==', 'pending')\
                .stream()
                
            for form in section_forms:
                form_data = form.to_dict()
                if session['email'] in form_data.get('approver_emails', []):
                    form_data['id'] = form.id
                    forms.append(form_data)
        
        # Get approved count
        approved_forms = db.collection('forms')\
            .where('student_section', 'in', session['sections'])\
            .where('status', '==', 'approved')\
            .stream()
        approved_count = sum(1 for _ in approved_forms)
    
    return render_template('faculty_dashboard.html', forms=forms, approved_count=approved_count)

@app.route('/hod/dashboard')
@login_required
@role_required(['hod'])
def hod_dashboard():
    forms = []
    if 'department' in session:
        forms_ref = db.collection('forms')\
            .where('student_department', '==', session['department'])\
            .where('status', '==', 'pending_hod')\
            .where('hod_status', '==', 'pending')\
            .stream()
        
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
        section_str = f"{session['year']}{session['section']}"
        
        form_data = {
            'form_type': form_type,
            'student_name': session['name'],
            'student_email': session['email'],
            'student_section': section_str,
            'student_department': session.get('department', ''),
            'student_year': session.get('year', ''),
            'reason': request.form['reason'],
            'status': 'pending',
            'hod_status': 'not_required',
            'timestamp': firestore.SERVER_TIMESTAMP,
            'approved_by': [],
            'approver_emails': []
        }

        if form_type in ['od', 'gate']:
            faculty_emails = request.form.getlist('faculty')
            if not faculty_emails:
                flash('Please select at least one faculty for approval', 'error')
                return redirect(url_for('submit_form', form_type=form_type))
            
            form_data['approver_emails'] = faculty_emails
            form_data['hod_status'] = 'pending'

        if form_type == 'od':
            # Validate time inputs
            start_time = request.form['start_time']
            end_time = request.form['end_time']
            
            try:
                start_dt = datetime.strptime(start_time, '%H:%M').time()
                end_dt = datetime.strptime(end_time, '%H:%M').time()
                
                # Validate college hours (9:00 to 16:00)
                if start_dt < time(9, 0) or end_dt > time(16, 0):
                    flash('Time must be between 9:00 and 16:00', 'error')
                    return redirect(url_for('submit_form', form_type=form_type))
                    
                if start_dt >= end_dt:
                    flash('End time must be after start time', 'error')
                    return redirect(url_for('submit_form', form_type=form_type))
                    
                # Calculate duration in hours and minutes
                start_min = start_dt.hour * 60 + start_dt.minute
                end_min = end_dt.hour * 60 + end_dt.minute
                duration_min = end_min - start_min
                duration_hours = duration_min // 60
                duration_minutes = duration_min % 60
                duration_str = f"{duration_hours}:{duration_minutes:02d}"
                
                form_data.update({
                    'date': request.form['date'],
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': duration_str
                })
            except ValueError:
                flash('Invalid time format', 'error')
                return redirect(url_for('submit_form', form_type=form_type))
                
        elif form_type == 'leave':
            coordinator_ref = db.collection('users')\
                .where('role', '==', 'faculty')\
                .where('department', '==', session['department'])\
                .where('coordinator_section', '==', section_str)\
                .limit(1).stream()
            
            coordinator = next(coordinator_ref, None)
            if coordinator:
                coordinator_data = coordinator.to_dict()
                form_data['approver_emails'] = [coordinator_data['email']]
            else:
                flash('No coordinator found for your section', 'error')
                return redirect(url_for('submit_form', form_type=form_type))
            
            form_data.update({
                'start_date': request.form['start_date'],
                'end_date': request.form['end_date'],
                'days': request.form['days']
            })
        elif form_type == 'gate':
            out_time = request.form['out_time']
            
            try:
                out_dt = datetime.strptime(out_time, '%H:%M').time()
                
                # Validate college hours (9:00 to 16:00)
                if out_dt < time(9, 0) or out_dt > time(16, 0):
                    flash('Time must be between 9:00 and 16:00', 'error')
                    return redirect(url_for('submit_form', form_type=form_type))
                    
                form_data.update({
                    'date': request.form['date'],
                    'out_time': out_time,
                    'duration': request.form['duration']
                })
            except ValueError:
                flash('Invalid time format', 'error')
                return redirect(url_for('submit_form', form_type=form_type))
        
        db.collection('forms').add(form_data)
        flash('Form submitted successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    faculty = []
    if form_type in ['od', 'gate'] and 'department' in session:
        section_str = f"{session['year']}{session['section']}"
        faculty_ref = db.collection('users')\
            .where('role', '==', 'faculty')\
            .where('department', '==', session['department'])\
            .where('sections', 'array_contains', section_str)\
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
    
    if session['email'] in form['approver_emails']:
        approved_by = list(set(form.get('approved_by', [])))
        
        if session['name'] not in approved_by:
            approved_by.append(session['name'])
            
            form_ref.update({
                'approved_by': approved_by
            })
            
            if len(approved_by) == len(set(form['approver_emails'])):
                if form['form_type'] in ['od', 'gate']:
                    form_ref.update({
                        'status': 'pending_hod',
                        'hod_status': 'pending'
                    })
                elif form['form_type'] == 'leave':
                    form_ref.update({
                        'status': 'approved',
                        'approved_at': firestore.SERVER_TIMESTAMP
                    })
            
            flash('Form approved successfully!', 'success')
        else:
            flash('You have already approved this form', 'warning')
    else:
        flash('You are not authorized to approve this form', 'error')
    
    return redirect(url_for('faculty_dashboard'))

@app.route('/reject/<form_id>')
@login_required
@role_required(['faculty'])
def reject(form_id):
    form_ref = db.collection('forms').document(form_id)
    form = form_ref.get().to_dict()
    
    if session['email'] in form['approver_emails']:
        form_ref.update({
            'status': 'rejected',
            'rejected_by': session['name'],
            'rejected_at': firestore.SERVER_TIMESTAMP,
            'rejection_reason': request.args.get('reason', 'No reason provided')
        })
        flash('Form has been rejected', 'warning')
    else:
        flash('You are not authorized to reject this form', 'error')
    
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

@app.route('/hod_reject/<form_id>')
@login_required
@role_required(['hod'])
def hod_reject(form_id):
    form_ref = db.collection('forms').document(form_id)
    form_ref.update({
        'status': 'rejected',
        'hod_status': 'rejected',
        'rejected_by': session['name'],
        'rejected_at': firestore.SERVER_TIMESTAMP,
        'rejection_reason': request.args.get('reason', 'No reason provided')
    })
    flash('Form has been rejected', 'warning')
    return redirect(url_for('hod_dashboard'))

@app.route('/approved_forms')
@login_required
def approved_forms():
    forms = []
    
    if session['role'] == 'student':
        forms_ref = db.collection('forms')\
            .where('student_email', '==', session['email'])\
            .where('status', '==', 'approved')\
            .stream()
    elif session['role'] == 'faculty':
        forms_ref = db.collection('forms')\
            .where('student_section', 'in', session.get('sections', []))\
            .where('status', '==', 'approved')\
            .stream()
    elif session['role'] == 'hod':
        forms_ref = db.collection('forms')\
            .where('student_department', '==', session.get('department', ''))\
            .where('status', '==', 'approved')\
            .stream()
    else:
        forms_ref = db.collection('forms')\
            .where('status', '==', 'approved')\
            .stream()
    
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