import os
import logging
from dotenv import load_dotenv
from pathlib import Path 


import imaplib
import smtplib
import email
import email.message
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import csv

import requests
from bs4 import BeautifulSoup

# atlas db
from pymongo import MongoClient



# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

def setup():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(), logging.FileHandler('main.log')])
    logging.info(f"Starting up at {time.strftime('%Y-%m-%d %H:%M:%S')}")

    global BOT_EMAIL, EMAIL_PASSWORD, IMAP_SERVER, IMAP_PORT, SMTP_SERVER, SMTP_PORT, DATA_DIR, CLIENTS_FILE, TIME_FILE, TIMEOUT, URL, DB_CONNECTION
    try:
        BOT_EMAIL = os.getenv('BOT_EMAIL')
        EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
        IMAP_SERVER = os.getenv('IMAP_SERVER')
        IMAP_PORT = os.getenv('IMAP_PORT')
        SMTP_SERVER = os.getenv('SMTP_SERVER')
        SMTP_PORT = os.getenv('SMTP_PORT')
        DATA_DIR = os.getenv('DATA_DIR')
        CLIENTS_FILE = os.getenv('CLIENTS_FILE')
        TIME_FILE = os.getenv('TIME_FILE')
        TIMEOUT = os.getenv('TIMEOUT')
        URL = os.getenv('URL')
        DB_CONNECTION = os.getenv('DB_CONNECTION')

        logging.info("Environment variables loaded.")
    except Exception as e:
        logging.critical(f"Error getting environment variables: {str(e)}")
        exit(1)

    # Get the location of the data files
    current_date = time.strftime("%Y-%m-%d")
    file_today = os.path.join(DATA_DIR, 'today.csv')
    file_yesterday = os.path.join(DATA_DIR, 'yesterday.csv')
    file_tomorrow = os.path.join(DATA_DIR, 'tomorrow.csv')
    file_clients = os.path.join(DATA_DIR, CLIENTS_FILE)
    file_time = os.path.join(DATA_DIR, TIME_FILE)
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logging.warning(f"Created {DATA_DIR} directory.")
    if not os.path.exists(file_clients):
        with open(file_clients, 'w', encoding="utf-8") as file:
            logging.warning(f"Created {CLIENTS_FILE}")
    if not os.path.exists(file_time):
        with open(file_time, 'w', encoding="utf-8") as file:
            file.write(current_date)
            logging.warning(f"Created {TIME_FILE}")
    if not os.path.exists(file_today):
        with open(file_today, 'w') as csvfile:
            logging.warning("Created today.csv")
    if not os.path.exists(file_tomorrow):
        with open(file_tomorrow, 'w') as csvfile:
            logging.warning("Created tomorrow.csv")
    if not os.path.exists(file_yesterday):
        with open(file_yesterday, 'w') as csvfile:
            logging.warning("Created yesterday.csv") 
    logging.info("Setup complete.")

def ctarf(): # Check time and rename files
    logging.info("Checking and renaming files...")
    current_date = time.strftime("%Y-%m-%d")
    
    file_today = os.path.join(DATA_DIR, 'today.csv')
    file_yesterday = os.path.join(DATA_DIR, 'yesterday.csv')
    file_tomorrow = os.path.join(DATA_DIR, 'tomorrow.csv')
    file_time = os.path.join(DATA_DIR, TIME_FILE)
    
    try:
        with open(file_time, 'r') as timefile:
            for row in timefile:
                date = row.strip()
                if date != current_date:
                    timefile.close()
                    with open(file_time, 'w') as timefile:
                        timefile.write(current_date)
                        logging.info("Updated date in time.txt")
                        timefile.close()
 
                    if os.path.exists(file_yesterday):
                        os.remove(file_yesterday)
                        logging.info("Deleted yesterday.csv")
                    os.rename(file_today, file_yesterday)
                    logging.info("Renamed today.csv to yesterday.csv")
                    if os.path.exists(file_tomorrow):
                        os.rename(file_tomorrow, file_today)
                        logging.info("Renamed tomorrow.csv to today.csv")
                else:
                    logging.info("Date is up to date.")
                timefile.close()
                break
        if not os.path.exists(file_tomorrow):
            with open(file_tomorrow, 'w', encoding="utf-8") as csvfile:
                logging.info("Created tomorrow.csv")
    
    except Exception as e:
        logging.error(str(e))
        return

def cw(url): # Check website
    logging.info("Checking website...")
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        table_today = soup.find('table', {'class': 'live today'})
        table_tomorrow = soup.find('table', {'class': 'live tomorrow'})
        
        # store the clients in a dictionary
        clients = {}
        with open(os.path.join(DATA_DIR, CLIENTS_FILE), 'r', encoding="utf-8") as clientsfile:
            for line in clientsfile:
                line = line.strip()
                if line:
                    email, name, class_, language = line.split(';')
                    clients[email] = (name, class_, language)
                    
        # store the today.csv in a list
        today = []
        with open(os.path.join(DATA_DIR, 'today.csv'), 'r', encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                line = line.split(',')
                today.append(line)
        file.close()
        
        if table_today is not None:
            logging.info("Today's table found.")
            '''
            file_today = os.path.join(DATA_DIR, 'today.csv')
            with open(file_today, 'w+', newline='', encoding="utf-8") as csvfile:
                # store the table in the file
                writer = csv.writer(csvfile)
                for row in table_today.find_all('tr'):
                    row = [i.text for i in row.find_all('td')]
                    writer.writerow(row)
                csvfile.close()
            '''
            # comapre the table with the today.csv
            table = []
            for row in table_today.find_all('tr'):
                row = [i.text for i in row.find_all('td')]
                table.append(row)
            
            # look for changes
            changes = []
            for i, row in enumerate(table):
                if i == 0:
                    continue
                if row not in today:
                    changes.append(row)
                    today.append(row)
            
            print(changes)
            # 
            
            
            # write the table to the file
            with open(os.path.join(DATA_DIR, 'today.csv'), 'w', newline='', encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                for row in today:
                    writer.writerow(row)
                csvfile.close()
                
    
    except Exception as e:
        logging.error(str(e))
        return
    
def reaa(): # Read emails and answer
    logging.info("Connected to IMAP server.")
    imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    imap.login(BOT_EMAIL, EMAIL_PASSWORD)
    imap.select("INBOX")

    # Search for unread emails
    status, email_ids = imap.search(None, 'UNSEEN')

    if status == "OK":
        email_ids = email_ids[0].split()
        num_unseen_emails = len(email_ids)
        logging.info(f"{num_unseen_emails} unseen emails.")
        
        for email_id in email_ids:
            # Fetch email message
            status, email_data = imap.fetch(email_id, '(RFC822)')
            
            if status == "OK":
                msg = email.message_from_bytes(email_data[0][1])

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            email_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                            sent_by_email = msg.get("From")
                            
                            if "Hello" in email_body or "Hello!" in email_body or "Hi" in email_body or "Hi!" in email_body or "Hey" in email_body or "Hey!" in email_body:
                                send_greeting_email(sent_by_email)
                                logging.info(f"Sent greeting email to {sent_by_email}")
                            
                            if "START" in email_body:
                                name = None
                                class_ = None
                                language = None
                                lines = email_body.split('\n')
                                for line in lines:
                                    if line.startswith("Name: "):
                                        name = line.split("Name: ")[1].strip()
                                    elif line.startswith("Class: "):
                                        class_ = line.split("Class: ")[1].strip()
                                    elif line.startswith("Language: "):
                                        language = line.split("Language: ")[1].strip()

                                if name and class_ and language:
                                    store_info(sent_by_email, name, class_, language)
                                    logging.info(f"Stored data for {name} ({class_}, {language})")
                                    send_confirmation_email(sent_by_email, name, class_, language)
                                    logging.info(f"Sent confirmation email to {sent_by_email}")
                                else:
                                    send_usage_instructions(sent_by_email)
                                    logging.info(f"Sent usage instructions to {sent_by_email}")
                            if "STOP" in email_body:
                                remove_data(sent_by_email)
                                logging.info(f"Removed data for {sent_by_email}")
                                send_stop_email(sent_by_email)
                                logging.info(f"Sent stop email to {sent_by_email}")
                            if "HELP" in email_body:
                                send_usage_instructions(sent_by_email)
                                logging.info(f"Sent usage instructions to {sent_by_email}")
            else:
                logging.error(f"Error fetching email with ID {email_id}.")
                return
    else:
        logging.error("Error getting emails.")
        return        

    imap.logout()
    logging.info("Logged out of IMAP server.")
    
def setup_mongo():
    # Connect to MongoDB Atlas
    client = MongoClient(DB_CONNECTION)
    db = client['master']
    collection = db['test']
    # dummy insert
    post = {"author": "Mike",
            "text": "My first blog post!",
            "tags": ["mongodb", "python", "pymongo"]}
    collection.insert_one(post)
    
    result = collection.find({})
    
    # print the length of the result this is a cursor object
    count = collection.count_documents({})
    print("\n\n")
    print(count)
    print("\n\n")
    
    
    for i in result:
        print(i)


def store_info(sender_email, name, class_, language):
    # Create a directory for data files if it doesn't exist
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    filename = os.path.join(DATA_DIR, CLIENTS_FILE)
    with open(filename, "a", encoding="utf-8") as file:
        class_ = class_.upper()
        language = language.lower()
        file.write(f"{sender_email};{name};{class_};{language}\n")

def remove_data(sender_email):
    # Create a temporary file to store data without the entry to be removed
    temp_filename = os.path.join(DATA_DIR, "temp_clients.txt")

    with open(os.path.join(DATA_DIR, CLIENTS_FILE), "r", encoding="utf-8") as file:
        lines = file.readlines()

    with open(temp_filename, "w", encoding="utf-8") as temp_file:
        removed = False
        for i, line in enumerate(lines):
            # Check if the line contains the sender's email
            if f"{sender_email};" in line:
                removed = True
                continue  # Skip this line to remove the data associated with the sender's email
            temp_file.write(line)

    # Replace the original data file with the temporary file
    os.replace(temp_filename, os.path.join(DATA_DIR, CLIENTS_FILE))

    if removed:
        print(f"Data associated with {sender_email} has been removed.")
    else:
        print(f"No data found for {sender_email}.")
    
def send_usage_instructions(send_to_email):
    # Connect to SMTP server
    smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    smtp.starttls()
    smtp.login(BOT_EMAIL, EMAIL_PASSWORD)

    # Compose HTML message with usage instructions and styles
    html_message = """
    <html>
    <head>
        <style>
            body {
                font-family: Arial, sans-serif;
            }
            ul {
                list-style-type: disc;
                margin-left: 20px;
            }
            li {
                margin-bottom: 10px;
            }
        </style>
    </head>
    <body>
        <p>To use this bot, please send an email with the following format in the body:</p>
        <p>Name:</strong> [Your Name]</p>
        <p>Class:</strong> [Your Class]</p>
        <p>Language:</strong> [Your second language]</p>
        <p>Example:</strong></p>
        <ul>
            <li><strong>Name:</strong> John Doe</li>
            <li><strong>Class:</strong> 11.be</li>
            <li><strong>Language:</strong> French</li>
        </ul>
    </body>
    </html>
    """

    # Create and send the response email with HTML content and styles
    msg = MIMEMultipart()
    msg.attach(MIMEText(html_message, 'html'))
    msg["Subject"] = "Re: START"
    msg["From"] = BOT_EMAIL
    msg["To"] = send_to_email

    smtp.sendmail(BOT_EMAIL, send_to_email, msg.as_string())

    smtp.quit()

def send_greeting_email(sender_email):
    # Connect to SMTP server
    smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    smtp.starttls()
    smtp.login(BOT_EMAIL, EMAIL_PASSWORD)

    # Compose HTML message with a stylish greeting
    html_message = """
    <html>
    <head>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f2f2f2;
                text-align: center;
                padding: 20px;
            }
            h1 {
                color: #333;
            }
            p {
                font-size: 18px;
                color: #555;
            }
        </style>
    </head>
    <body>
        <h1>Hello there!</h1>
        <p>Welcome to our bot. We're glad you're here.</p>
    </body>
    </html>
    """

    # Create and send the greeting email with HTML content and styles
    msg = MIMEMultipart()
    msg.attach(MIMEText(html_message, 'html'))
    msg["Subject"] = "Welcome to Our Bot"
    msg["From"] = BOT_EMAIL
    msg["To"] = sender_email

    smtp.sendmail(BOT_EMAIL, sender_email, msg.as_string())

    smtp.quit()

def send_confirmation_email(sender_email, name, class_, language):
    # Connect to SMTP server
    smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    smtp.starttls()
    smtp.login(BOT_EMAIL, EMAIL_PASSWORD)

    # Compose HTML message with a styled confirmation
    html_message = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f2f2f2;
                text-align: center;
                padding: 20px;
            }}
            h1 {{
                color: #333;
            }}
            p {{
                font-size: 18px;
                color: #555;
            }}
        </style>
    </head>
    <body>
        <h1>Thank you for registering, {name}!</h1>
        <p>Your class is {class_} and your second language is {language}.</p>
        <p>We look forward to serving you.</p>
    </body>
    </html>
    """

    # Create and send the confirmation email with HTML content and styles
    msg = MIMEMultipart()
    msg.attach(MIMEText(html_message, 'html'))
    msg["Subject"] = "Thank you for registering!"
    msg["From"] = BOT_EMAIL
    msg["To"] = sender_email

    smtp.sendmail(BOT_EMAIL, sender_email, msg.as_string())

    smtp.quit()

def send_stop_email(sender_email):
    # Connect to SMTP server
    smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    smtp.starttls()
    smtp.login(BOT_EMAIL, EMAIL_PASSWORD)

    # Compose HTML message with a styled farewell
    html_message = """
    <html>
    <head>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f2f2f2;
                text-align: center;
                padding: 20px;
            }
            h1 {
                color: #333;
            }
            p {
                font-size: 18px;
                color: #555;
            }
        </style>
    </head>
    <body>
        <h1>We are sorry to see you go!</h1>
        <p>Thank you for using our services. If you ever decide to come back, we'll be here for you.</p>
    </body>
    </html>
    """

    # Create and send the farewell email with HTML content and styles
    msg = MIMEMultipart()
    msg.attach(MIMEText(html_message, 'html'))
    msg["Subject"] = "Farewell and Goodbye"
    msg["From"] = BOT_EMAIL
    msg["To"] = sender_email

    smtp.sendmail(BOT_EMAIL, sender_email, msg.as_string())

    smtp.quit()
    
if __name__ == "__main__":
    setup()
    print(setup_mongo())
    reaa()
    ctarf()
    cw(URL)
    