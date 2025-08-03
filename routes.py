from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.security import check_password_hash, generate_password_hash
from app import app, db
from models import User, QRCode, Attendance, EmailLog
from datetime import datetime, date, time
import pytz
import logging
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Indian Standard Time
IST = pytz.timezone('Asia/Kolkata')
from qr_service import generate_monthly_qr_codes, get_today_qr_code, create_qr_code_image
from email_service import send_attendance_email

@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('faculty_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('faculty_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    # Get statistics
    total_faculty = User.query.filter_by(role='faculty').count()
    today_attendance = Attendance.query.filter_by(date=date.today()).count()
    
    # Get recent attendances
    recent_attendances = db.session.query(Attendance, User).join(User).filter(
        Attendance.date == date.today()
    ).order_by(Attendance.scan_time.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html', 
                         total_faculty=total_faculty,
                         today_attendance=today_attendance,
                         recent_attendances=recent_attendances)

@app.route('/admin/register_faculty', methods=['GET', 'POST'])
def register_faculty():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        full_name = request.form['full_name']
        department = request.form['department']
        password = request.form['password']
        
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            flash('Username or email already exists', 'error')
        else:
            new_faculty = User(
                username=username,
                email=email,
                full_name=full_name,
                department=department,
                password_hash=generate_password_hash(password),
                role='faculty'
            )
            db.session.add(new_faculty)
            db.session.commit()
            flash(f'Faculty {full_name} registered successfully! Username: {username}, Password: {password}', 'success')
            return redirect(url_for('admin_dashboard'))
    
    return render_template('register_faculty.html')

@app.route('/admin/generate_qr')
def generate_qr():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    try:
        qr_codes = generate_monthly_qr_codes()
        flash(f'Generated {len(qr_codes)} QR codes for the month', 'success')
    except Exception as e:
        flash(f'Error generating QR codes: {str(e)}', 'error')
        logging.error(f"QR generation error: {e}")
    
    # Get today's QR code to display
    today_qr = get_today_qr_code()
    
    return render_template('generate_qr.html', today_qr=today_qr)

@app.route('/faculty/dashboard')
def faculty_dashboard():
    if 'user_id' not in session or session.get('role') != 'faculty':
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Check if user has already marked attendance today
    today_attendance = Attendance.query.filter_by(
        user_id=user.id,
        date=date.today()
    ).first()
    
    # Check if current time is within attendance window (9:30 AM - 9:45 AM IST)
    ist_now = datetime.now(IST)
    current_time = ist_now.time()
    attendance_start = time(9, 30)  # 9:30 AM
    attendance_end = time(9, 45)    # 9:45 AM
    
    can_mark_attendance = (attendance_start <= current_time <= attendance_end) and not today_attendance
    
    return render_template('faculty_dashboard.html', 
                         user=user,
                         today_attendance=today_attendance,
                         can_mark_attendance=can_mark_attendance,
                         current_time=current_time)

@app.route('/faculty/scan_qr')
def scan_qr():
    if 'user_id' not in session or session.get('role') != 'faculty':
        return redirect(url_for('login'))
    
    # Check if current time is within attendance window (IST)
    ist_now = datetime.now(IST)
    current_time = ist_now.time()
    attendance_start = time(9, 30)
    attendance_end = time(9, 45)
    
    if not (attendance_start <= current_time <= attendance_end):
        flash('Attendance can only be marked between 9:30 AM and 9:45 AM (IST)', 'error')
        return redirect(url_for('faculty_dashboard'))
    
    # Check if already marked attendance today
    today_attendance = Attendance.query.filter_by(
        user_id=session['user_id'],
        date=date.today()
    ).first()
    
    if today_attendance:
        flash('You have already marked attendance for today', 'error')
        return redirect(url_for('faculty_dashboard'))
    
    return render_template('scan_qr.html')

@app.route('/api/verify_qr', methods=['POST'])
def verify_qr():
    if 'user_id' not in session or session.get('role') != 'faculty':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    scanned_code = data.get('code')
    
    if not scanned_code:
        return jsonify({'success': False, 'message': 'No QR code provided'})
    
    # Check if current time is within attendance window (IST)
    ist_now = datetime.now(IST)
    current_time = ist_now.time()
    attendance_start = time(9, 30)
    attendance_end = time(9, 45)
    
    if not (attendance_start <= current_time <= attendance_end):
        return jsonify({'success': False, 'message': 'Attendance window closed (9:30-9:45 AM IST)'})
    
    # Verify QR code
    today_qr = get_today_qr_code()
    if not today_qr or today_qr.code != scanned_code:
        return jsonify({'success': False, 'message': 'Invalid QR code'})
    
    # Check if already marked attendance
    existing_attendance = Attendance.query.filter_by(
        user_id=session['user_id'],
        date=date.today()
    ).first()
    
    if existing_attendance:
        return jsonify({'success': False, 'message': 'Already marked attendance today'})
    
    # Mark attendance
    attendance = Attendance(
        user_id=session['user_id'],
        qr_code_id=today_qr.id,
        date=date.today(),
        status='present'
    )
    
    db.session.add(attendance)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Attendance marked successfully'})

@app.route('/admin/send_email')
def send_email():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    try:
        result = send_attendance_email()
        if result:
            flash('Attendance email sent successfully', 'success')
        else:
            flash('Failed to send attendance email', 'error')
    except Exception as e:
        flash(f'Error sending email: {str(e)}', 'error')
        logging.error(f"Email sending error: {e}")
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/download_qr/<date_str>')
def download_qr(date_str):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    try:
        from datetime import datetime
        qr_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        qr_code = QRCode.query.filter_by(date=qr_date).first()
        
        if not qr_code:
            flash('QR code not found for this date', 'error')
            return redirect(url_for('generate_qr'))
        
        # Create QR code image
        qr_img = create_qr_code_image(qr_code.code)
        
        # Save to BytesIO
        from io import BytesIO
        img_io = BytesIO()
        qr_img.save(img_io, 'PNG')
        img_io.seek(0)
        
        from flask import send_file
        return send_file(
            img_io,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'qr_code_{date_str}.png'
        )
        
    except Exception as e:
        flash(f'Error downloading QR code: {str(e)}', 'error')
        logging.error(f"QR download error: {e}")
        return redirect(url_for('generate_qr'))

@app.route('/admin/download_app')
@admin_required
def download_app():
    """Download the complete application as a ZIP file"""
    try:
        import zipfile
        import tempfile
        from datetime import datetime
        
        # Create temporary ZIP file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        # Files to include in the download
        files_to_include = [
            'app.py', 'main.py', 'routes.py', 'models.py',
            'email_service.py', 'qr_service.py', 'scheduler.py',
            'setup.py', 'README.md'
        ]
        
        # Template and static files
        template_files = []
        static_files = []
        
        # Get template files
        import os
        if os.path.exists('templates'):
            for file in os.listdir('templates'):
                if file.endswith('.html'):
                    template_files.append(os.path.join('templates', file))
        
        # Get static files
        if os.path.exists('static'):
            for root, dirs, files in os.walk('static'):
                for file in files:
                    static_files.append(os.path.join(root, file))
        
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add main application files
            for file in files_to_include:
                if os.path.exists(file):
                    zipf.write(file, file)
            
            # Add template files
            for file in template_files:
                if os.path.exists(file):
                    zipf.write(file, file)
            
            # Add static files
            for file in static_files:
                if os.path.exists(file):
                    zipf.write(file, file)
            
            # Create a sample .env file
            env_sample = """# Smart Attendance System Configuration
# Replace with your actual values

SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SESSION_SECRET=your_secret_key_here
DATABASE_URL=sqlite:///attendance.db
"""
            zipf.writestr('.env.sample', env_sample)
            
            # Create installation instructions
            install_txt = """Smart Attendance System - Installation Instructions

1. Extract this ZIP file to a folder
2. Install Python 3.8 or higher
3. Run: python setup.py (this will install all required packages)
4. Copy .env.sample to .env and edit with your credentials
5. Run: python main.py
6. Access at http://localhost:5000
7. Login with admin/admin123

For Gmail setup:
- Enable 2-Factor Authentication
- Generate App Password for Mail
- Use app password in .env file

Email recipients can be changed in email_service.py
Attendance window can be modified in routes.py and scheduler.py
"""
            zipf.writestr('INSTALL.txt', install_txt)
        
        temp_zip.close()
        
        # Generate filename with current date
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f'smart_attendance_system_{date_str}.zip'
        
        return send_file(
            temp_zip.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/zip'
        )
        
    except Exception as e:
        flash(f'Error creating download: {str(e)}', 'error')
        logging.error(f"App download error: {e}")
        return redirect(url_for('admin_dashboard'))






