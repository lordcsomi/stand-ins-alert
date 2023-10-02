import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText

# URL of the website with the table
url = 'https://apps.karinthy.hu/helyettesites/is'

# Email configuration
sender_email = 'your_email@gmail.com'
receiver_email = 'your_email@gmail.com'  # Change to your own email address
smtp_server = 'smtp.gmail.com'
smtp_port = 587
smtp_username = 'your_email@gmail.com'
smtp_password = 'your_email_password'  # Use an App Password if you have 2-factor authentication enabled

# Function to send an email
def send_email(subject, message):
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        # Connect to the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)

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

        # Locate the table
        table = soup.find('table', {'class': 'live today'})

        # Get the number of rows in the table
        rows = table.find_all('tr')

        # Check if the number of rows has increased (indicating a new entry)
        if len(rows) > previous_row_count:
            send_email("New Entry Detected", "A new entry has been added to the table.")
            # Update the previous_row_count to the current count
            global previous_row_count
            previous_row_count = len(rows)
    except Exception as e:
        print("Error:", str(e))

# Initial row count
previous_row_count = 0

# Run the script continuously (you can use a scheduler or cron job for periodic execution)
while True:
    check_table_for_changes()
