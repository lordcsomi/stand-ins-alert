import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from decouple import config
import time


# Get email credentials from environment variables
sender_email = config('SENDER_EMAIL')
receiver_email = config('RECEIVER_EMAIL')
password = config('EMAIL_PASSWORD')

# URL of the website with the table
url = 'https://apps.karinthy.hu/helyettesites'

# Function to send an email
def send_email(subject, message):
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        # Connect to the SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)

        # Send the email
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print("Email sending failed:", str(e))

# Function to check for changes in the table
def check_table_for_changes():
    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url)

        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')
        print(soup)

        # Locate the table
        table = soup.find('table', {'class': 'live today'})

        # Get the number of rows in the table
        rows = table.find_all('tr')

        # Check if the number of rows has increased (indicating a new entry)
        if len(rows) > check_table_for_changes.previous_row_count:
            send_email("New Entry Detected", "A new entry has been added to the table.")
            # Update the previous_row_count to the current count
            check_table_for_changes.previous_row_count = len(rows)
    except Exception as e:
        print("Error:", str(e))

# Initial row count
check_table_for_changes.previous_row_count = 0

# Time interval in seconds (e.g., check every 5 minutes)
interval_seconds = 300

# Run the script continuously
'''
while True:
    check_table_for_changes()
    time.sleep(interval_seconds)
'''

check_table_for_changes()
