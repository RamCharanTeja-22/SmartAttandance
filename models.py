from app import db
from datetime import datetime
from sqlalchemy.sql import func

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='faculty')  # 'admin' or 'faculty'
    full_name = db.Column(db.String(100), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=func.now())
    
    def __repr__(self):
        return f'<User {self.username}>'

class QRCode(db.Model):
    __tablename__ = 'qr_code'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(255), unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())
    
    def __repr__(self):
        return f'<QRCode {self.code} for {self.date}>'

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    qr_code_id = db.Column(db.Integer, db.ForeignKey('qr_code.id'), nullable=False)
    scan_time = db.Column(db.DateTime, default=func.now())
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='present')  # 'present' or 'absent'
    
    # Relationships
    user = db.relationship('User', backref='attendances')
    qr_code = db.relationship('QRCode', backref='attendances')
    
    def __repr__(self):
        return f'<Attendance {self.user.username} on {self.date}>'

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    recipients = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    sent_at = db.Column(db.DateTime, default=func.now())
    status = db.Column(db.String(20), default='sent')  # 'sent' or 'failed'
    
    def __repr__(self):
        return f'<EmailLog {self.subject} on {self.date}>'
