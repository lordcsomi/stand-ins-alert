import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from decouple import config
import time

# Get email credentials from environment variables
sender_email = config('SENDER_EMAIL')
receiver_email = config('RECEIVER_EMAIL')
password = config('EMAIL_PASSWORD')

url = 'https://apps.karinthy.hu/helyettesites'

def send_email_with_table(table_html):
    subject = "Table Update Detected"
    
    # Create an email message with HTML content
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    # Create an HTML part for the email
    html = f"""
    <html>
    <body>
        <h2>Table Update Detected</h2>
        {table_html}
    </body>
    </html>
    """
    
    # Attach the HTML content to the email
    msg.attach(MIMEText(html, 'html'))
    
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

def check_table_for_changes():
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'live tomorrow'})

        if table is not None:
            rows = table.find_all('tr')
            
            # Create an HTML table to hold the data
            table_html = '<table border="1">'
            
            # Add table headers
            table_html += '<tr>'
            table_html += '<th>Helyettesítő tanár</th>'
            table_html += '<th>Óra</th>'
            table_html += '<th>Oszt.</th>'
            table_html += '<th>Tárgy</th>'
            table_html += '<th>Terem</th>'
            table_html += '<th>Helyettesítendő tanár</th>'
            table_html += '<th>Megjegyzés</th>'
            table_html += '</tr>'
            
            for row in rows[1:]:
                stand_in = row.find('td', {'class': 'stand_in'}).text.strip()
                lesson = row.find('td', {'class': 'lesson'}).text.strip()
                class_name = row.find('td', {'class': 'class'}).text.strip()
                subject = row.find('td', {'class': 'subject'}).text.strip()
                room = row.find('td', {'class': 'room'}).text.strip()
                missing_teacher = row.find('td', {'class': 'missing_teacher'}).text.strip()
                comment = row.find('td', {'class': 'comment'}).text.strip()
                
                # Check if at least one of the fields is not empty
                if (stand_in != '' or lesson != '' or class_name != '' or subject != '' or room != '' or missing_teacher != '' or comment != ''):
                    # Add row to the HTML table
                    table_html += '<tr>'
                    table_html += f'<td>{stand_in}</td>'
                    table_html += f'<td>{lesson}</td>'
                    table_html += f'<td>{class_name}</td>'
                    table_html += f'<td>{subject}</td>'
                    table_html += f'<td>{room}</td>'
                    table_html += f'<td>{missing_teacher}</td>'
                    table_html += f'<td>{comment}</td>'
                    table_html += '</tr>'
            
            table_html += '</table>'
            
            # Send email with the formatted table
            send_email_with_table(table_html)
    except Exception as e:
        print("Error:", str(e))

# Initial row count
check_table_for_changes.previous_row_count = 0

check_table_for_changes()
