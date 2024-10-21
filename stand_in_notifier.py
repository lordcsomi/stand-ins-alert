# stand_in_notifier.py

import os
import logging
import requests
from bs4 import BeautifulSoup
import smtplib
import imaplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email_validator import validate_email, EmailNotValidError
from datetime import datetime, timedelta
import schedule
import time
from sqlalchemy import create_engine, Column, Integer, String, Date, UniqueConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# ---------------------------------------
# Configuration
# ---------------------------------------

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(override=True)

# Email configuration
BOT_EMAIL = os.getenv('BOT_EMAIL')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
IMAP_SERVER = os.getenv('IMAP_SERVER')
IMAP_PORT = int(os.getenv('IMAP_PORT', '993'))
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))

# Database configuration
DB_TYPE = os.getenv('DB_TYPE', 'postgresql')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Application configuration
URL = os.getenv('URL')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '5'))  # in minutes
EMAIL_CHECK_INTERVAL = int(os.getenv('EMAIL_CHECK_INTERVAL', '1'))  # in minutes

# Telegram configuration (if used)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Discord configuration (if used)
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# ---------------------------------------
# Logging Configuration
# ---------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# ---------------------------------------
# Database Setup
# ---------------------------------------

# Construct the database URL
DATABASE_URL = f"{DB_TYPE}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create the engine
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

# ---------------------------------------
# Database Models
# ---------------------------------------

class ScheduleEntry(Base):
    __tablename__ = 'schedule_entries'
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    stand_in_teacher = Column(String)
    lesson = Column(String)
    class_name = Column(String, index=True)
    subject = Column(String)
    room = Column(String)
    missing_teacher = Column(String)
    comment = Column(String)
    __table_args__ = (
        UniqueConstraint('date', 'lesson', 'class_name', 'missing_teacher', name='_schedule_uc'),
    )

class Client(Base):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    class_name = Column(String)
    language = Column(String)

def init_db():
    """Initializes the database by creating tables."""
    Base.metadata.create_all(bind=engine)
    logging.info("Database initialized.")

# ---------------------------------------
# Utility Functions
# ---------------------------------------

def validate_email_address(email_address):
    """Validates an email address."""
    try:
        valid = validate_email(email_address)
        return valid.email
    except EmailNotValidError as e:
        logging.error(f"Invalid email address: {email_address} - {e}")
        return None

# ---------------------------------------
# Web Scraper
# ---------------------------------------

def fetch_webpage(url):
    """Fetches the webpage content."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        logging.info(f"Fetched webpage: {url}")
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching webpage: {e}")
        return None

def parse_html(html):
    """Parses the HTML content and extracts schedule data."""
    soup = BeautifulSoup(html, 'html.parser')
    schedules = {}

    for table in soup.find_all('table', class_='live'):
        date_caption = table.caption.get_text(strip=True)
        date = date_caption.split(',')[0]  # Extract the date

        schedule = []
        tbody = table.find('tbody')

        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            if cells and len(cells) == 7:
                entry = {
                    'stand_in_teacher': cells[0].get_text(strip=True),
                    'lesson': cells[1].get_text(strip=True),
                    'class': cells[2].get_text(strip=True),
                    'subject': cells[3].get_text(strip=True),
                    'room': cells[4].get_text(strip=True),
                    'missing_teacher': cells[5].get_text(strip=True),
                    'comment': cells[6].get_text(strip=True),
                }
                schedule.append(entry)

        schedules[date] = schedule

    logging.info("Parsed HTML content.")
    return schedules

# ---------------------------------------
# Email Handler
# ---------------------------------------

def read_emails():
    """Reads emails from the inbox and processes commands."""
    logging.info("Checking for new emails...")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(BOT_EMAIL, EMAIL_PASSWORD)
        mail.select('inbox')

        result, data = mail.search(None, '(UNSEEN)')
        mail_ids = data[0].split()
        logging.info(f"Found {len(mail_ids)} new emails.")

        if not mail_ids:
            logging.info("No new emails found.")
            return

        for mail_id in mail_ids:
            result, message_data = mail.fetch(mail_id, '(RFC822)')
            raw_email = message_data[0][1]
            email_message = email.message_from_bytes(raw_email)

            process_email(email_message)

            # Mark email as seen
            mail.store(mail_id, '+FLAGS', '\\Seen')

        mail.logout()
    except Exception as e:
        logging.error(f"Error reading emails: {e}")

def process_email(email_message):
    """Processes an individual email message."""
    from_email = email.utils.parseaddr(email_message['From'])[1]
    subject = email_message['Subject']
    body = get_email_body(email_message)

    logging.info(f"Processing email from {from_email} with subject '{subject}'.")

    if "START" in subject.upper():
        handle_start_command(from_email, body)
    elif "STOP" in subject.upper():
        handle_stop_command(from_email)
    elif "HELP" in subject.upper():
        send_usage_instructions(from_email)
    else:
        logging.info(f"Unknown command from {from_email}.")

def get_email_body(email_message):
    """Extracts the body from an email message."""
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == 'text/plain':
                return part.get_payload(decode=True).decode('utf-8', errors='ignore')
    else:
        return email_message.get_payload(decode=True).decode('utf-8', errors='ignore')

def handle_start_command(from_email, body):
    """Handles the START command to register a new client."""
    name, class_name, language = parse_client_info(body)
    if name and class_name and language:
        store_client_info(from_email, name, class_name, language)
        send_confirmation_email(from_email, name, class_name, language)
    else:
        send_usage_instructions(from_email)

def handle_stop_command(from_email):
    """Handles the STOP command to remove a client."""
    remove_client_data(from_email)
    send_stop_email(from_email)

def parse_client_info(body):
    """Parses client information from the email body."""
    lines = body.strip().split('\n')
    name = class_name = language = None

    for line in lines:
        if line.startswith("Name:"):
            name = line.split("Name:")[1].strip()
        elif line.startswith("Class:"):
            class_name = line.split("Class:")[1].strip().upper()
        elif line.startswith("Language:"):
            language = line.split("Language:")[1].strip().lower()

    return name, class_name, language

def store_client_info(email_address, name, class_name, language):
    """Stores or updates client information in the database."""
    session = SessionLocal()
    email_address = validate_email_address(email_address)
    if not email_address:
        logging.error(f"Invalid email address: {email_address}")
        return

    try:
        # Check if client already exists
        client = session.query(Client).filter(Client.email == email_address).first()
        if client:
            # Update existing client information
            client.name = name
            client.class_name = class_name
            client.language = language
            session.commit()
            logging.info(f"Updated client info for: {email_address}")
        else:
            # Create new client
            client = Client(
                email=email_address,
                name=name,
                class_name=class_name,
                language=language
            )
            session.add(client)
            session.commit()
            logging.info(f"Registered new client: {email_address}")
    except Exception as e:
        session.rollback()
        logging.error(f"Error storing client info: {e}")
    finally:
        session.close()

def remove_client_data(email_address):
    """Removes client data from the database."""
    session = SessionLocal()
    try:
        client = session.query(Client).filter(Client.email == email_address).first()
        if client:
            session.delete(client)
            session.commit()
            logging.info(f"Removed client data for: {email_address}")
        else:
            logging.info(f"No client data found for: {email_address}")
    except Exception as e:
        session.rollback()
        logging.error(f"Error removing client data: {e}")
    finally:
        session.close()

def send_email(to_email, subject, html_content):
    """Sends an email with HTML content."""
    msg = MIMEMultipart()
    msg.attach(MIMEText(html_content, 'html'))
    msg['Subject'] = subject
    msg['From'] = BOT_EMAIL
    msg['To'] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(BOT_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)
        logging.info(f"Sent email to {to_email} with subject '{subject}'.")
    except Exception as e:
        logging.error(f"Error sending email to {to_email}: {e}")

def send_usage_instructions(to_email):
    """Sends usage instructions to the client."""
    html_content = """
    <html>
    <body>
        <p>To register for notifications, please send an email with the subject 'START' and the following information in the body:</p>
        <p>Name: [Your Name]<br>
        Class: [Your Class]<br>
        Language: [Your Second Language]</p>
        <p>Example:</p>
        <p>Name: John Doe<br>
        Class: 10.BE<br>
        Language: English</p>
        <p>To unsubscribe, send an email with the subject 'STOP'.</p>
    </body>
    </html>
    """
    send_email(to_email, "Usage Instructions", html_content)

def send_confirmation_email(to_email, name, class_name, language):
    """Sends a confirmation email to the client."""
    html_content = f"""
    <html>
    <body>
        <p>Dear {name},</p>
        <p>You have been successfully registered for notifications.</p>
        <p>Class: {class_name}<br>
        Language: {language}</p>
        <p>Thank you!</p>
    </body>
    </html>
    """
    send_email(to_email, "Registration Confirmation", html_content)

def send_stop_email(to_email):
    """Sends a farewell email to the client."""
    html_content = """
    <html>
    <body>
        <p>You have been unsubscribed from notifications.</p>
        <p>We're sorry to see you go.</p>
    </body>
    </html>
    """
    send_email(to_email, "Unsubscription Confirmation", html_content)

# ---------------------------------------
# Notifier
# ---------------------------------------

def compose_message(entries, is_new=True):
    """Composes a notification message from schedule entries, returns HTML content."""
    messages = []
    status = "🆕 Lesson Change" if is_new else "✏️ Updated Entry"

    # Get today's date and tomorrow's date
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    for entry in entries:
        entry_date = entry.date
        # Check if the date is today or tomorrow
        date_str = entry_date.strftime('%Y-%m-%d')
        if entry_date == today:
            date_str += " (Today)"
        elif entry_date == tomorrow:
            date_str += " (Tomorrow)"

        # Build the HTML content for the entry
        msg = f"""
        <div style="border:1px solid #ccc; padding:15px; margin-bottom:15px; border-radius:10px;">
            <h2 style="color:#2E86C1;">{status}</h2>
            <p style="font-size:18px;"><strong>📅 Date:</strong> {date_str}</p>
            <p style="font-size:18px;"><strong>🏫 Class:</strong> {entry.class_name}</p>
            <p style="font-size:18px;"><strong>📖 Lesson:</strong> {entry.lesson}</p>
            <p style="font-size:18px;"><strong>🧪 Subject:</strong> {entry.subject}</p>
            <p style="font-size:18px;"><strong>👩‍🏫 Stand-in Teacher:</strong> {entry.stand_in_teacher}</p>
            <p style="font-size:18px;"><strong>❌👨‍🏫 Missing Teacher:</strong> {entry.missing_teacher}</p>
            <p style="font-size:18px;"><strong>🚪 Room:</strong> {entry.room}</p>
            <p style="font-size:18px;"><strong>💬 Comment:</strong> {entry.comment}</p>
        </div>
        """
        messages.append(msg)

    # Combine the messages
    html_content = f"""
    <html>
    <body>
        <div style="font-family:Arial, sans-serif; font-size:16px; color:#333;">
            {''.join(messages)}
        </div>
    </body>
    </html>
    """
    return html_content

def send_notifications(clients, message):
    """Sends notifications to clients via their preferred channels."""
    for client in clients:
        # Send email notification
        send_email(client.email, "Schedule Update", message)

        # Implement Telegram notification if needed
        # send_telegram_message(client.telegram_chat_id, message)

        # Implement Discord notification if needed
        # send_discord_message(client.discord_webhook_url, message)

    logging.info(f"Sent notifications to {len(clients)} clients.")

def notify_clients(entries, is_new=True):
    """Notifies clients about new or updated schedule entries."""
    session = SessionLocal()
    class_entries = {}
    for entry in entries:
        class_entries.setdefault(entry.class_name, []).append(entry)

    for class_name, entries in class_entries.items():
        clients = session.query(Client).filter(Client.class_name == class_name).all()
        if clients:
            message = compose_message(entries, is_new)
            send_notifications(clients, message)
        else:
            logging.info(f"No clients found for class {class_name}.")

    session.close()


# ---------------------------------------
# Scheduler
# ---------------------------------------

def check_website():
    """Checks the website for updates and processes new entries or updates existing ones."""
    logging.info("Checking website for updates...")
    html = fetch_webpage(URL)
    if html is None:
        logging.error("Failed to fetch webpage.")
        return

    schedules = parse_html(html)
    session = SessionLocal()

    for date_str, entries in schedules.items():
        date_obj = parse_date(date_str)
        if date_obj is None:
            continue

        new_entries = []
        updated_entries = []

        for entry_data in entries:
            # Skip entries that have missing critical information
            if not entry_data['lesson'] or not entry_data['class'] or not entry_data['missing_teacher']:
                continue

            existing_entry = session.query(ScheduleEntry).filter_by(
                date=date_obj,
                lesson=entry_data['lesson'],
                class_name=entry_data['class'],
                missing_teacher=entry_data['missing_teacher']
            ).first()

            if not existing_entry:
                # Add new entry
                entry = ScheduleEntry(
                    date=date_obj,
                    stand_in_teacher=entry_data['stand_in_teacher'],
                    lesson=entry_data['lesson'],
                    class_name=entry_data['class'],
                    subject=entry_data['subject'],
                    room=entry_data['room'],
                    missing_teacher=entry_data['missing_teacher'],
                    comment=entry_data['comment']
                )
                session.add(entry)
                new_entries.append(entry)
                logging.info(f"New entry added: {entry_data}")
            else:
                # Check for updates
                changes = []
                if existing_entry.stand_in_teacher != entry_data['stand_in_teacher']:
                    existing_entry.stand_in_teacher = entry_data['stand_in_teacher']
                    changes.append('stand_in_teacher')
                if existing_entry.room != entry_data['room']:
                    existing_entry.room = entry_data['room']
                    changes.append('room')
                if existing_entry.comment != entry_data['comment']:
                    existing_entry.comment = entry_data['comment']
                    changes.append('comment')
                if changes:
                    session.commit()  # Commit after updating the entry
                    updated_entries.append((existing_entry, changes))
                    logging.info(f"Entry updated: {entry_data}, Changes: {changes}")

        # Commit session after processing all entries
        session.commit()

        # Notify clients about new and updated entries
        if new_entries:
            notify_clients(new_entries, is_new=True)
        if updated_entries:
            updated_entries_list = [entry for entry, _ in updated_entries]
            notify_clients(updated_entries_list, is_new=False)

    session.close()
    logging.info("Website check complete.")

def start_scheduler():
    """Starts the scheduler to run tasks at specified intervals."""
    # debugging
    check_website()
    read_emails()

    schedule.every(CHECK_INTERVAL).minutes.do(check_website)
    schedule.every(EMAIL_CHECK_INTERVAL).minutes.do(read_emails)

    logging.info("Scheduler started.")

    while True:
        schedule.run_pending()
        time.sleep(1)

def parse_date(date_str):
    """Parses date string to a datetime.date object using a replace dictionary."""
    # Replace dictionary for Hungarian to English month names
    replace_dict = {
        'január': 'January',
        'február': 'February',
        'március': 'March',
        'április': 'April',
        'május': 'May',
        'június': 'June',
        'július': 'July',
        'augusztus': 'August',
        'szeptember': 'September',
        'október': 'October',
        'november': 'November',
        'december': 'December'
    }

    # Replace Hungarian month names with English equivalents
    for hu_month, en_month in replace_dict.items():
        date_str = date_str.replace(hu_month, en_month)

    try:
        date_obj = datetime.strptime(date_str, '%Y. %B %d.').date()
        return date_obj
    except ValueError as e:
        logging.error(f"Error parsing date '{date_str}': {e}")
        return None

# ---------------------------------------
# Main Entry Point
# ---------------------------------------

def main():
    logging.info("Application started.")
    init_db()
    start_scheduler()

if __name__ == '__main__':
    main()
