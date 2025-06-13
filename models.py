# models.py

from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from db import Base  # <-- сюда

class User(Base):
    __tablename__ = "users"
    id                = Column(Integer, primary_key=True, index=True)
    username          = Column(String, unique=True, nullable=False)
    password          = Column(String, nullable=False)
    balance           = Column(Float, default=0.0)
    commission_earned = Column(Float, default=0.0)

class Ad(Base):
    __tablename__ = "ads"
    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id"))
    type             = Column(String, nullable=False)
    crypto           = Column(String, nullable=False)
    fiat             = Column(String, nullable=False)
    amount           = Column(Float, nullable=False)
    price            = Column(Float, nullable=False)
    min_limit        = Column(Float, nullable=False)
    max_limit        = Column(Float, nullable=False)
    payment_methods  = Column(Text, nullable=False)
    user_rating      = Column(Float, default=100.0)
    user             = relationship("User")

class Order(Base):
    __tablename__ = "orders"
    id         = Column(Integer, primary_key=True, index=True)
    buyer_id   = Column(Integer, ForeignKey("users.id"))
    ad_id      = Column(Integer, ForeignKey("ads.id"))
    amount     = Column(Float, nullable=False)
    status     = Column(String, default="waiting")
    created_at = Column(String, nullable=False)
    buyer      = relationship("User", foreign_keys=[buyer_id])
    ad         = relationship("Ad")

class Message(Base):
    __tablename__ = "messages"
    id        = Column(Integer, primary_key=True, index=True)
    order_id  = Column(Integer, ForeignKey("orders.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    text      = Column(Text,   nullable=False)
    timestamp = Column(String, nullable=False)
    sender    = relationship("User")
    order     = relationship("Order")
