# Digital Forms System

A comprehensive web-based form submission and approval system for educational institutions. This application allows students to submit OD (On Duty), Leave, and Gate Pass forms, which are then reviewed and approved by faculty members and HODs (Head of Department).

## 📋 Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [User Roles](#user-roles)
- [Features by Role](#features-by-role)
- [Development](#development)
- [Contributing](#contributing)

## ✨ Features

### Core Functionality
- **Multi-role Authentication System** - Student, Faculty, HOD, and Admin roles
- **Form Submission** - Submit OD, Leave, and Gate Pass forms
- **Multi-level Approval Workflow** - Faculty → HOD approval process
- **Real-time Form Tracking** - View form status and approval progress
- **Search & Filter** - Search approved forms by multiple criteria
- **Pagination** - Efficiently handle large numbers of forms
- **Responsive Design** - Works seamlessly on desktop and mobile devices

### Student Features
- Submit OD forms with date, time, and duration
- Apply for leave with start/end dates
- Request gate pass with exit time and duration
- Select multiple faculty members for approval
- View all approved forms with detailed information
- Track submission and approval timestamps

### Faculty Features
- View pending forms from assigned sections
- Approve or reject student forms
- Track approval progress
- View all approved forms from their sections

### HOD Features
- Final approval authority for OD and Gate Pass forms
- View all pending forms from their department
- Approve or reject forms after faculty approval
- Access to department-wide approved forms

### Admin Features
- User management system
- Edit user roles and permissions
- Search and filter users
- System-wide oversight

## 🛠 Technology Stack

### Backend
- **Python 3.x** - Programming language
- **Flask** - Web framework
- **Firebase Admin SDK** - Backend services
- **Firestore** - NoSQL database
- **Python-dotenv** - Environment variable management

### Frontend
- **HTML5** - Markup
- **CSS3** - Styling (with CSS Variables)
- **JavaScript** - Client-side interactivity
- **Material Icons** - Icon library
- **Poppins Font** - Typography

### Deployment
- **Gunicorn** - WSGI HTTP Server

## 📁 Project Structure

```
college-form/
│
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── firebase_config.json        # Firebase configuration (example)
├── .env                        # Environment variables (create this)
├── README.md                   # Project documentation
│
├── static/                     # Static files
│   ├── css/
│   │   └── common.css         # Shared CSS styles
│   └── js/
│       └── form_submission.js # Form submission logic
│
└── templates/                  # HTML templates
    ├── login.html             # Login page
    ├── register.html          # Registration page
    ├── loading.html           # Loading screen
    ├── student_dashboard.html # Student dashboard
    ├── faculty_dashboard.html # Faculty dashboard
    ├── hod_dashboard.html     # HOD dashboard
    ├── admin_dashboard.html   # Admin dashboard
    ├── submit_form.html       # Form submission page
    ├── approved_forms.html    # Approved forms listing
    └── admin_edit_user.html   # Admin user edit page
```

## 🚀 Installation

### Prerequisites
- Python 3.7 or higher
- Firebase project with Firestore enabled
- Firebase service account credentials

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd "college form"
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set Up Firebase
1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Enable Firestore Database
3. Generate a service account key:
   - Go to Project Settings → Service Accounts
   - Click "Generate New Private Key"
   - Save the JSON file securely

### Step 5: Configure Environment Variables
Create a `.env` file in the project root:

```env
# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here

# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/...
```

**Important:** Keep your `.env` file secure and never commit it to version control.

## ⚙️ Configuration

### Firestore Database Structure

The application uses the following Firestore collections:

#### `users` Collection
```
users/{email}
  - name: string
  - email: string
  - password: string (in production, use hashed passwords)
  - role: string (student, faculty, hod, admin)
  - department: string
  - year: string (for students)
  - section: string (for students)
  - sections: array (for faculty)
  - coordinator_section: string (optional, for faculty)
  - created_at: timestamp
```

#### `forms` Collection
```
forms/{formId}
  - form_type: string (od, leave, gate)
  - student_name: string
  - student_email: string
  - student_section: string
  - student_department: string
  - student_year: string
  - reason: string
  - status: string (pending, pending_hod, approved, rejected)
  - hod_status: string (not_required, pending, approved, rejected)
  - approver_emails: array
  - approved_by: array
  - timestamp: timestamp
  - approved_at: timestamp
  - date: string (for od, gate)
  - start_time: string (for od)
  - end_time: string (for od)
  - duration: string
  - start_date: string (for leave)
  - end_date: string (for leave)
  - days: string (for leave)
  - out_time: string (for gate)
```

## 📖 Usage

### Starting the Application

#### Development Mode
```bash
python app.py
```

The application will be available at `http://localhost:5000`

#### Production Mode
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### First Time Setup

1. **Register an Admin User**
   - Start the application
   - Go to the registration page
   - Register with admin credentials
   - Manually set the role to "admin" in Firestore

2. **Create User Accounts**
   - Log in as admin
   - Use the admin dashboard to manage users
   - Assign roles: Student, Faculty, HOD, or Admin

3. **Configure Faculty Sections**
   - Edit faculty users in admin dashboard
   - Assign sections they can approve forms for
   - Set coordinator sections if applicable

## 👥 User Roles

### Student
- Can submit OD, Leave, and Gate Pass forms
- Select faculty members for approval
- View their own approved forms
- Track form submission status

### Faculty
- Approve/reject forms from assigned sections
- View pending forms requiring their approval
- Track approval progress
- View approved forms from their sections

### HOD (Head of Department)
- Final approval authority for OD and Gate Pass forms
- Approve/reject forms after faculty approval
- View all department forms
- Access department-wide approved forms

### Admin
- Full system access
- User management (create, edit, delete)
- Role assignment
- Search and filter users
- System configuration

## 🎯 Features by Role

### Form Submission Process

#### OD Form (On Duty)
1. Student selects date, start time (09:00-16:30), and end time
2. Duration is automatically calculated
3. Student selects one or more faculty members
4. Faculty members approve the form
5. After all faculty approvals, form goes to HOD
6. HOD provides final approval

#### Leave Form
1. Student selects start and end dates
2. Number of days is automatically calculated
3. Form is routed to section coordinator
4. Coordinator approves/rejects
5. No HOD approval required

#### Gate Pass
1. Student selects date and exit time
2. Student enters duration in hours
3. Student selects one or more faculty members
4. Faculty members approve the form
5. After all faculty approvals, form goes to HOD
6. HOD provides final approval

### Approved Forms Features
- **Sorting**: Latest approved forms appear first
- **Search**: Search by student name, email, reason, section, or form type
- **Filter**: Filter by form type (OD, Leave, Gate Pass)
- **Pagination**: View 10 forms per page
- **Detailed View**: Complete form information with timestamps
- **Responsive Design**: Works on all devices

## 🔒 Security Considerations

### Production Recommendations
1. **Password Hashing**: Implement password hashing (bcrypt, Argon2)
2. **HTTPS**: Always use HTTPS in production
3. **Environment Variables**: Never commit `.env` files
4. **Firebase Rules**: Configure proper Firestore security rules
5. **Input Validation**: Add server-side input validation
6. **CSRF Protection**: Implement CSRF tokens
7. **Rate Limiting**: Add rate limiting for API endpoints

### Current Security Features
- Session-based authentication
- Role-based access control
- Environment variable configuration
- Secure Firebase credentials management

## 🛠 Development

### Running Tests
```bash
# Add your test commands here
python -m pytest
```

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add comments for complex logic
- Maintain consistent indentation

### Debugging
Enable debug mode in development:
```python
if __name__ == '__main__':
    app.run(debug=True)
```

**Note:** Never run with `debug=True` in production!

## 📝 API Routes

### Authentication
- `GET/POST /login` - User login
- `GET/POST /register` - User registration
- `GET /logout` - User logout
- `GET /loading` - Loading screen

### Dashboards
- `GET /dashboard` - Role-based dashboard redirect
- `GET /student/dashboard` - Student dashboard
- `GET /faculty/dashboard` - Faculty dashboard
- `GET /hod/dashboard` - HOD dashboard
- `GET /admin/dashboard` - Admin dashboard

### Forms
- `GET/POST /submit_form/<form_type>` - Submit form (od/leave/gate)
- `GET /approved_forms` - View approved forms
- `GET /approve/<form_id>` - Approve form (Faculty)
- `GET /reject/<form_id>` - Reject form (Faculty)
- `GET /hod_approve/<form_id>` - Approve form (HOD)
- `GET /hod_reject/<form_id>` - Reject form (HOD)

### Admin
- `GET/POST /admin/edit_user/<email>` - Edit user
- `GET /admin/search_users` - Search users

## 🐛 Troubleshooting

### Common Issues

**Issue:** Firebase connection error
- **Solution:** Check Firebase credentials in `.env` file
- Verify service account has proper permissions

**Issue:** Forms not appearing
- **Solution:** Check Firestore security rules
- Verify user has correct role and section assignments

**Issue:** Timestamps not displaying
- **Solution:** Ensure Firestore timestamps are properly converted
- Check datetime formatting in templates

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 Support

For support, email bjakash2006@example.com or create an issue in the repository.

## 🙏 Acknowledgments

- Firebase for backend services
- Flask community for excellent documentation
- Material Icons for iconography
- Poppins font from Google Fonts

---

**Note:** This is a development version. For production deployment, ensure all security best practices are implemented.

