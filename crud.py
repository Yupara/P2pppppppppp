# crud.py

from sqlalchemy.orm import Session
from datetime import datetime

import models

def create_order(db: Session, ad: models.Ad, buyer: models.User):
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

def pay_order(db: Session, order: models.Order, user: models.User):
    if order.buyer_id != user.id or order.status != "waiting":
        raise ValueError("Нельзя оплатить")
    order.status = "paid"
    db.commit()
    return order

def confirm_order(db: Session, order: models.Order, user: models.User, admin_user: models.User):
    if order.ad.user_id != user.id or order.status != "paid":
        raise ValueError("Нельзя подтвердить")
    commission = order.amount * 0.005
    seller_amount = order.amount - commission
    seller = user
    buyer = order.buyer

    if seller.balance < order.amount:
        raise ValueError("Недостаточно средств у продавца")

    seller.balance           -= order.amount
    buyer.balance            += seller_amount
    admin_user.commission_earned += commission

    order.status = "confirmed"
    db.commit()
    return order

def dispute_order(db: Session, order: models.Order, user: models.User):
    if order.status not in ("waiting", "paid"):
        raise ValueError("Нельзя открыть спор")
    order.status = "dispute"

    # Увеличиваем счётчик отмен и блокируем при 10+
    buyer = order.buyer
    buyer.cancel_count += 1
    if buyer.cancel_count >= 10:
        buyer.is_blocked = True

    db.commit()
    return order

def get_messages(db: Session, order_id: int):
    return db.query(models.Message)\
             .filter(models.Message.order_id == order_id)\
             .order_by(models.Message.id)\
             .all()

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
