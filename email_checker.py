import os
import imaplib
import smtplib
import email
from decouple import config

# Load environment variables from .env file
SENDER_EMAIL = config('SENDER_EMAIL')
EMAIL_PASSWORD = config('EMAIL_PASSWORD')

# IMAP settings
IMAP_SERVER = "imap.gmail.com"  # Update with your email provider's IMAP server
IMAP_PORT = 993

# SMTP settings
SMTP_SERVER = "smtp.gmail.com"  # Update with your email provider's SMTP server
SMTP_PORT = 587

# Directory to store data files
DATA_DIR = "data"
DATA_FILE = "clients.txt"

def read_email():
    # Connect to IMAP server
    imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    imap.login(SENDER_EMAIL, EMAIL_PASSWORD)
    imap.select("INBOX")

    # Search for unread emails
    status, email_ids = imap.search(None, 'UNSEEN')

    if status == "OK":
        email_ids = email_ids[0].split()
        num_unseen_emails = len(email_ids)
        print(f"You have {num_unseen_emails} unseen emails.")
        
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
                                print("Sent greeting email.")
                            
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
                                    store_data(sent_by_email, name, class_, language)
                                    print(f"Stored data for {name} ({class_}, {language})")
                                    send_confirmation_email(sent_by_email, name, class_, language)
                                    print("Sent confirmation email.")
                                else:
                                    send_usage_instructions(sent_by_email)
                                    print("Sent usage instructions.")
                            if "STOP" in email_body:
                                remove_data(sent_by_email)
                                print("Removed data.")
                                send_stop_email(sent_by_email)
                                print("Sent stop email.")
                                

    imap.logout()

def store_data(sender_email, name, class_, language):
    # Create a directory for data files if it doesn't exist
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    filename = os.path.join(DATA_DIR, DATA_FILE)
    with open(filename, "a", encoding="utf-8") as file:
        file.write(f"{sender_email};{name};{class_};{language}\n")

def remove_data(sender_email):
    # Create a temporary file to store data without the entry to be removed
    temp_filename = os.path.join(DATA_DIR, "temp_clients.txt")

    with open(os.path.join(DATA_DIR, DATA_FILE), "r", encoding="utf-8") as file:
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
    os.replace(temp_filename, os.path.join(DATA_DIR, DATA_FILE))

    if removed:
        print(f"Data associated with {sender_email} has been removed.")
    else:
        print(f"No data found for {sender_email}.")
    
def send_usage_instructions(send_to_email):
    # Connect to SMTP server
    smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    smtp.starttls()
    smtp.login(SENDER_EMAIL, EMAIL_PASSWORD)

    # Compose response message with usage instructions
    response_message = (
        "To use this bot, please send an email with the following format in the body:\n"
        "START\n"
        "Name: [Your Name]\n"
        "Class: [Your Class]\n"
        "Language: [Your second language]\n"
        "----- Example -----\n"
        "Name: John Doe\n"
        "Class: 11.be\n"
        "Language: French\n"
    )

    # Create and send the response email
    msg = email.message.EmailMessage()
    msg.set_content(response_message)
    msg["Subject"] = "Re: START"
    msg["From"] = SENDER_EMAIL
    msg["To"] = send_to_email

    smtp.send_message(msg)

    smtp.quit()

def send_greeting_email(sender_email):
    # Connect to SMTP server
    smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    smtp.starttls()
    smtp.login(SENDER_EMAIL, EMAIL_PASSWORD)

    # Compose response message with data
    response_message = (
        f"Hello there!\n"
    )

    # Create and send the response email
    msg = email.message.EmailMessage()
    msg.set_content(response_message)
    msg["Subject"] = "Re: Hello"
    msg["From"] = SENDER_EMAIL
    msg["To"] = sender_email

    smtp.send_message(msg)

    smtp.quit()

def send_confirmation_email(sender_email, name, class_, language):
    # Connect to SMTP server
    smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    smtp.starttls()
    smtp.login(SENDER_EMAIL, EMAIL_PASSWORD)

    # Compose response message with data
    response_message = (
        f"Thank you for registering, {name}!\n"
        f"Your class is {class_} and your second language is {language}.\n"
    )

    # Create and send the response email
    msg = email.message.EmailMessage()
    msg.set_content(response_message)
    msg["Subject"] = "Thank you for registering!"
    msg["From"] = SENDER_EMAIL
    msg["To"] = sender_email

    smtp.send_message(msg)

    smtp.quit()

def send_stop_email(sender_email):
    # Connect to SMTP server
    smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    smtp.starttls()
    smtp.login(SENDER_EMAIL, EMAIL_PASSWORD)

    # Compose response message with data
    response_message = (
        f"We are sorry to see you go!\n"
    )

    # Create and send the response email
    msg = email.message.EmailMessage()
    msg.set_content(response_message)
    msg["Subject"] = "Re: STOP"
    msg["From"] = SENDER_EMAIL
    msg["To"] = sender_email

    smtp.send_message(msg)

    smtp.quit()

if __name__ == "__main__":
    read_email()
