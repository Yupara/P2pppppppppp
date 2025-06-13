# сюда складываем функции отправки email/SMS
def send_sms(to: str, text: str):
    # TODO: интеграция с провайдером
    pass

def send_email(to: str, subject: str, html: str):
    # TODO: интеграция с SMTP
    pass

# фоновый таск ежедневной статистики, крупные сделки, споры

# notifications.py

import smtplib
from email.mime.text import MIMEText

SMTP_HOST = "smtp.example.com"
SMTP_PORT = 587
SMTP_USER = "user@example.com"
SMTP_PASS = "password"

def send_email(to: str, subject: str, html: str):
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)
