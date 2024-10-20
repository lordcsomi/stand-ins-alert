
# Stand-In Notifier

This application monitors the school's stand-in schedule webpage and notifies subscribed clients about relevant changes via email. It can also be configured to send notifications through other channels like Telegram or Discord if needed.

## **Features**

- Scrapes the school's stand-in schedule webpage.
- Detects changes relevant to specific classes.
- Sends notifications via email.
- Stores data in a PostgreSQL database.
- Handles client email commands (START, STOP, HELP).
- Runs scheduled tasks to check for updates.

## **File Structure**

```
stand-ins-alert/
├── stand_in_notifier.py
├── .env
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
└── app.log
```

## **Setup Instructions**

### **1. Clone the Repository**

```bash
git clone https://github.com/lordcsomi/stand-ins-alert.git
cd stand-ins-alert
```

### **2. Set Up the Virtual Environment**

```bash
python3 -m venv env
source env/bin/activate
```

### **3. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **4. Configure Environment Variables**

- Create a `.env` file in the root directory.
- Populate it with your configuration variables.

Example `.env` file:

```ini
# Email configuration
BOT_EMAIL=your_bot_email@example.com
EMAIL_PASSWORD=your_email_password
IMAP_SERVER=imap.example.com
IMAP_PORT=993
SMTP_SERVER=smtp.example.com
SMTP_PORT=587

# Database configuration
DB_TYPE=postgresql
DB_HOST=localhost  # Use 'db' if using Docker Compose
DB_PORT=5432
DB_NAME=stand_in_schedule
DB_USER=your_db_username
DB_PASSWORD=your_db_password

# Application configuration
URL=https://apps.karinthy.hu/helyettesites/
CHECK_INTERVAL=5
EMAIL_CHECK_INTERVAL=1

# Optional: Telegram configuration
# TELEGRAM_BOT_TOKEN=your_telegram_bot_token
# TELEGRAM_CHAT_ID=your_telegram_chat_id

# Optional: Discord configuration
# DISCORD_WEBHOOK_URL=your_discord_webhook_url
```

### **5. Run the Application**

```bash
python stand_in_notifier.py
```

### **6. Using Docker (Optional)**

#### **Build the Docker Image**

```bash
docker build -t stand_in_notifier:latest .
```

#### **Run the Docker Container**

```bash
docker run -d --env-file .env stand_in_notifier:latest
```

#### **Using Docker Compose**

```bash
docker-compose up -d
```

## **Usage**

- **Register as a Client:**
  - Send an email to the bot's email address with the subject `START` and include your name, class, and language in the body.

    Example:
    ```
    Name: John Doe
    Class: 10.BE
    Language: English
    ```

- **Unsubscribe:**
  - Send an email with the subject `STOP` to the bot's email address.

- **Get Help:**
  - Send an email with the subject `HELP` to receive usage instructions.

## **Troubleshooting**

- **Database Connection Errors:**
  - Ensure PostgreSQL is running and accessible.
  - Verify database credentials in the `.env` file.

- **Email Sending Errors:**
  - Check SMTP configuration.
  - Ensure the email account allows SMTP access.

- **Web Scraping Errors:**
  - Verify the URL in the `.env` file.
  - Check if the website's structure has changed.

## **Contributing**

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit them (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Submit a pull request.

## **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
