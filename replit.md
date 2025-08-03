# Overview

This is a Smart Attendance System designed for college faculty members. The system allows administrators to manage faculty attendance through QR code scanning. Faculty members can mark their attendance by scanning daily QR codes during a specific time window (9:30 AM - 9:35 AM). The system automatically generates unique QR codes for each day of the month and sends daily attendance reports via email to administrators.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Web Framework
- **Flask-based web application** with SQLAlchemy ORM for database operations
- **Session-based authentication** using Flask's built-in session management
- **Role-based access control** with two user types: admin and faculty
- **Template-based frontend** using Jinja2 templating with Bootstrap for responsive UI

## Database Design
- **SQLite database** for local data storage with four main entities:
  - Users (faculty and admin accounts with role-based permissions)
  - QR Codes (daily unique codes with date validation)
  - Attendance (tracking faculty check-ins with timestamps)
  - Email Logs (audit trail for sent reports)
- **Automatic table creation** on application startup with default admin user provisioning

## QR Code System
- **Daily QR code generation** with 32-character random strings for security
- **Monthly bulk generation** to ensure codes are available for the entire month
- **Time-restricted validation** limiting attendance marking to a 5-minute window (9:30-9:35 AM)
- **Date-specific codes** preventing reuse across different days

## Attendance Workflow
- **Web-based QR scanner** using device camera with JavaScript QR detection
- **Manual code entry fallback** for devices without camera access
- **Real-time attendance validation** checking time windows and duplicate entries
- **Status tracking** with present/absent classification

## Email Automation
- **Scheduled daily reports** sent automatically at 9:45 AM IST using threading
- **SMTP integration** via Gmail servers with environment variable configuration
- **HTML-formatted reports** showing present and absent faculty lists with scan times in IST
- **Excel and PDF attachments** with detailed attendance data, color-coded present/absent status
- **Multi-recipient support** for administrative staff (nlramcharanplacement@gmail.com, 2224m1a3133@vemu.org)

## Security Features
- **Password hashing** using Werkzeug's security utilities
- **Session-based authentication** with role verification for protected routes
- **Unique QR codes** with date validation to prevent unauthorized attendance
- **Time window enforcement** limiting when attendance can be marked

## Admin Functions
- **Faculty management** with registration and user administration
- **Attendance reporting** with daily and historical views
- **QR code generation** with manual regeneration capabilities
- **Dashboard analytics** showing attendance statistics and rates

# External Dependencies

## Email Service
- **Gmail SMTP** servers for sending attendance reports
- **Environment variables** for email credentials (SMTP_EMAIL, SMTP_PASSWORD)
- **Configurable recipient lists** for administrative notifications

## Frontend Libraries
- **Bootstrap CSS framework** via CDN for responsive design
- **Font Awesome icons** for enhanced UI elements
- **jsQR library** for client-side QR code scanning functionality

## Python Packages
- **Flask** web framework with SQLAlchemy for database operations
- **Werkzeug** for password hashing and security utilities
- **Schedule library** for automated task scheduling with IST timezone support
- **smtplib** for email delivery functionality
- **openpyxl** for Excel file generation with styled attendance reports
- **reportlab** for PDF generation with formatted attendance tables

## Development Tools
- **Environment-based configuration** for database URLs and email settings
- **Debug mode** enabled for development with detailed error logging
- **Static file serving** for CSS and JavaScript assets