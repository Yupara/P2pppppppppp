# models.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    Text,
    Boolean,
    DateTime
)
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base  # Ваш declarative_base из db.py

class User(Base):
    __tablename__ = "users"
    id                   = Column(Integer, primary_key=True, index=True)
    username             = Column(String, unique=True, nullable=False)
    password             = Column(String, nullable=False)
    balance              = Column(Float, default=0.0)
    commission_earned    = Column(Float, default=0.0)

    # Платёжные данные
    card_number          = Column(String, nullable=True)
    card_holder          = Column(String, nullable=True)
    wallet_address       = Column(String, nullable=True)
    wallet_network       = Column(String, nullable=True)

    # Блокировка и споры
    cancel_count         = Column(Integer, default=0)
    is_blocked           = Column(Boolean, default=False)

    # Верификация
    phone                = Column(String, nullable=True)
    phone_code           = Column(String, nullable=True)
    is_phone_verified    = Column(Boolean, default=False)
    passport_filename    = Column(String, nullable=True)
    is_passport_verified = Column(Boolean, default=False)

    # Реферальная система
    referrer_id          = Column(Integer, ForeignKey("users.id"), nullable=True)
    referrals            = relationship("User", remote_side=[id])

class Ad(Base):
    __tablename__ = "ads"
    id                = Column(Integer, primary_key=True, index=True)
    user_id           = Column(Integer, ForeignKey("users.id"))
    type              = Column(String, nullable=False)    # "buy" или "sell"
    crypto            = Column(String, nullable=False)
    fiat              = Column(String, nullable=False)
    amount            = Column(Float, nullable=False)
    price             = Column(Float, nullable=False)
    min_limit         = Column(Float, nullable=False)
    max_limit         = Column(Float, nullable=False)
    payment_methods   = Column(Text,   nullable=False)    # CSV, например "sber,tinkoff"
    user_rating       = Column(Float, default=100.0)
    user              = relationship("User")

class Order(Base):
    __tablename__ = "orders"
    id         = Column(Integer, primary_key=True, index=True)
    buyer_id   = Column(Integer, ForeignKey("users.id"))
    ad_id      = Column(Integer, ForeignKey("ads.id"))
    amount     = Column(Float, nullable=False)
    status     = Column(String, default="waiting")        # waiting, paid, confirmed, dispute
    created_at = Column(DateTime, default=datetime.utcnow)
    buyer      = relationship("User", foreign_keys=[buyer_id])
    ad         = relationship("Ad")

class Message(Base):
    __tablename__ = "messages"
    id        = Column(Integer, primary_key=True, index=True)
    order_id  = Column(Integer, ForeignKey("orders.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    text      = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sender    = relationship("User")
    order     = relationship("Order")

class Dispute(Base):
    __tablename__ = "disputes"
    id         = Column(Integer, primary_key=True, index=True)
    order_id   = Column(Integer, ForeignKey("orders.id"))
    user_id    = Column(Integer, ForeignKey("users.id"))
    reason     = Column(Text, nullable=False)
    status     = Column(String, default="open")          # open, resolved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    order      = relationship("Order")
    user       = relationship("User")

class Notification(Base):
    __tablename__ = "notifications"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"))
    message    = Column(Text, nullable=False)
    is_read    = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user       = relationship("User")
