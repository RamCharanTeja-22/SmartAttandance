import schedule
import time
import threading
from datetime import datetime, time as dt_time
import pytz
from email_service import send_attendance_email
import logging

# Indian Standard Time
IST = pytz.timezone('Asia/Kolkata')

def should_send_email():
    """Check if it's time to send email in IST"""
    now_ist = datetime.now(IST)
    return now_ist.hour == 9 and now_ist.minute == 45

def schedule_daily_email():
    """Schedule daily email at 9:45 AM IST"""
    last_sent_date = None
    
    while True:
        now_ist = datetime.now(IST)
        current_date = now_ist.date()
        
        # Check if it's 9:45 AM IST and we haven't sent today's email yet
        if (now_ist.hour == 9 and now_ist.minute == 45 and 
            last_sent_date != current_date):
            
            logging.info(f"Sending daily email at {now_ist.strftime('%Y-%m-%d %H:%M:%S IST')}")
            success = send_attendance_email()
            
            if success:
                last_sent_date = current_date
                logging.info("Daily email sent successfully")
            else:
                logging.error("Failed to send daily email")
        
        time.sleep(60)  # Check every minute

def start_scheduler():
    """Start the scheduler in a separate thread"""
    scheduler_thread = threading.Thread(target=schedule_daily_email, daemon=True)
    scheduler_thread.start()
    logging.info("Email scheduler started")

# Auto-start scheduler when module is imported
if __name__ != '__main__':
    start_scheduler()
