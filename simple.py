import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from decouple import config

def send_email():
    # Load email configuration from .env file
    sender_email = config('SENDER_EMAIL')
    receiver_email = config('RECEIVER_EMAIL')
    password = config('EMAIL_PASSWORD')

    # Create a MIMEText object to represent the email body
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = 'Subject of the email'

    # Email body
    body = "This is the email body."
    message.attach(MIMEText(body, 'plain'))

    # SMTP server setup
    smtp_server = 'smtp.gmail.com'  # Change this to your email provider's SMTP server
    smtp_port = 587  # Change this to your email provider's SMTP port

    # Create a secure connection to the SMTP server
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, password)

        # Send the email
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        print("Email sent successfully!")
    except Exception as e:
        print("Error sending email:", str(e))
    finally:
        # Close the SMTP server connection
        server.quit()

# Call the function to send an email
for i in range(5):
    send_email()
