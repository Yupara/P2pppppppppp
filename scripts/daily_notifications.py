from datetime import datetime
from models import Trade
from database import get_db
import smtplib
from email.mime.text import MIMEText

def send_daily_notification(admin_email):
    db = next(get_db())
    today = datetime.utcnow().date()
    trades = db.query(Trade).filter(Trade.status == "completed").all()
    
    # Подсчитываем комиссию
    total_commission = sum(trade.amount * 0.005 for trade in trades if trade.created_at.date() == today)
    
    # Отправляем уведомление
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    from_email = "your_email@example.com"
    password = "your_email_password"
    
    msg = MIMEText(f"Сегодня вы заработали: {total_commission:.2f} USDT.")
    msg["Subject"] = "Ежедневный отчет о заработке"
    msg["From"] = from_email
    msg["To"] = admin_email
    
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, [admin_email], msg.as_string())

# Запуск функции
if __name__ == "__main__":
    admin_email = "admin@example.com"
    send_daily_notification(admin_email)
