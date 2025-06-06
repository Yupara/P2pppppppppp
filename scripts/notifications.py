import smtplib
from email.mime.text import MIMEText

def send_email_notification(to_email, subject, body):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    from_email = "your_email@example.com"
    password = "your_email_password"
    
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, [to_email], msg.as_string())

def notify_large_trade(user_email, trade_id, amount):
    subject = "Large Trade Notification"
    body = f"A large trade (ID: {trade_id}) of {amount} USDT has been initiated."
    send_email_notification(user_email, subject, body)

def notify_dispute(user_email, trade_id):
    subject = "Dispute Notification"
    body = f"A dispute has been opened for trade ID: {trade_id}. Please check the admin panel."
    send_email_notification(user_email, subject, body)
