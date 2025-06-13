# crud.py

from sqlalchemy.orm import Session
from datetime import datetime, timedelta

import models

# Создать заказ (сделку)
def create_order(db: Session, ad: models.Ad, buyer: models.User):
    # заморозка средств продавца не нужна, тк списание при подтверждении
    order = models.Order(
        buyer_id=buyer.id,
        ad_id=ad.id,
        amount=ad.amount,
        status="waiting",
        created_at=datetime.utcnow().isoformat()
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

# Пометить как «оплачен»
def pay_order(db: Session, order: models.Order, user: models.User):
    if order.buyer_id != user.id or order.status != "waiting":
        raise ValueError("Нельзя оплатить")
    order.status = "paid"
    db.commit()
    return order

# Подтвердить получение — финальный расчёт и комиссионка
def confirm_order(db: Session, order: models.Order, user: models.User, admin_user: models.User):
    # только продавец может подтвердить
    if order.ad.user_id != user.id or order.status != "paid":
        raise ValueError("Нельзя подтвердить")
    # комиссия 0.5%
    commission = order.amount * 0.005
    seller_amount = order.amount - commission
    seller = user
    buyer = order.buyer

    # Проверка баланса продавца (на случай, если списываем с баланса)
    if seller.balance < order.amount:
        raise ValueError("Недостаточно средств у продавца")

    # Перевод средств
    seller.balance -= order.amount
    buyer.balance += seller_amount
    admin_user.commission_earned += commission

    order.status = "confirmed"
    db.commit()
    return order

# Открыть спор — помечаем и замораживаем
def dispute_order(db: Session, order: models.Order, user: models.User):
    if order.status not in ("waiting", "paid"):
        raise ValueError("Нельзя открыть спор")
    order.status = "dispute"
    db.commit()
    return order

# Получение списка сообщений
def get_messages(db: Session, order_id: int):
    return db.query(models.Message).filter(models.Message.order_id == order_id).order_by(models.Message.id).all()

# Добавление сообщения
def add_message(db: Session, order_id: int, sender_id: int, text: str):
    msg = models.Message(
        order_id=order_id,
        sender_id=sender_id,
        text=text,
        timestamp=datetime.utcnow().isoformat()
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
