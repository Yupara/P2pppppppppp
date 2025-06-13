# tasks.py

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

import models
from db import SessionLocal
from notifications import send_email  # Ваша функция отправки писем

# Порог крупной сделки (в USDT)
LARGE_ORDER_THRESHOLD = 10_000.0

def daily_commission_report():
    db: Session = SessionLocal()
    try:
        # За вчерашний день
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        # Предполагается, что у админа (id=1) хранится commission_earned суммарно
        admin = db.query(models.User).get(1)
        total = admin.commission_earned
        subject = f"Отчет комиссии за {yesterday.isoformat()}"
        body = f"Ваша комиссия за {yesterday.isoformat()} составила {total:.2f} USDT."
        send_email(to="you@example.com", subject=subject, html=body)
    finally:
        db.close()

def large_order_alerts():
    db: Session = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=5)
        recent_orders = (
            db.query(models.Order)
              .filter(models.Order.created_at >= cutoff)
              .filter(models.Order.amount >= LARGE_ORDER_THRESHOLD)
              .all()
        )
        for order in recent_orders:
            subj = f"Крупная сделка #{order.id}"
            body = (
                f"Сделка #{order.id}: {order.amount} {order.ad.crypto} "
                f"по курсу {order.ad.price} {order.ad.fiat}."
            )
            send_email(to="you@example.com", subject=subj, html=body)
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Каждый день в 00:10 UTC
    scheduler.add_job(daily_commission_report, 'cron', hour=0, minute=10)
    # Каждые 5 минут
    scheduler.add_job(large_order_alerts, 'interval', minutes=5)
    scheduler.start()

if __name__ == "__main__":
    start_scheduler()
    # Чтобы задачи работали вместе с приложением, импортируйте и вызовите start_scheduler() в app.py
