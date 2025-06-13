# tasks.py

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

import models
from db import SessionLocal
from notifications import send_email  # ваша функция отправки email

# Порог крупной сделки
LARGE_ORDER_THRESHOLD = 10_000.0

def daily_commission_report():
    db: Session = SessionLocal()
    try:
        today = datetime.utcnow().date()
        # Считаем комиссию за вчера
        start = datetime.combine(today - timedelta(days=1), datetime.min.time())
        end   = datetime.combine(today,          datetime.min.time())
        total = db.query(models.User).filter(models.User.id == 1).first().commission_earned
        # TODO: вместо commission_earned хранить по датам
        text = f"Ваша комиссия за {start.date()} составила {total:.2f} USDT."
        send_email(to="you@example.com", subject="Ежедневный отчёт комиссии", html=text)
    finally:
        db.close()

def large_order_alerts():
    db: Session = SessionLocal()
    try:
        # Ищем сделки за последние 5 минут больше порога
        cutoff = datetime.utcnow() - timedelta(minutes=5)
        orders = db.query(models.Order).filter(
            models.Order.created_at >= cutoff.isoformat(),
            models.Order.amount >= LARGE_ORDER_THRESHOLD
        ).all()
        for o in orders:
            body = (
                f"Найдена крупная сделка #{o.id}: "
                f"{o.amount} {o.ad.crypto} по курсу {o.ad.price} {o.ad.fiat}."
            )
            send_email(to="you@example.com", subject="Крупная сделка P2P", html=body)
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Запуск каждый день в 00:10 UTC
    scheduler.add_job(daily_commission_report, 'cron', hour=0, minute=10)
    # Запуск каждые 5 минут
    scheduler.add_job(large_order_alerts, 'interval', minutes=5)
    scheduler.start()
