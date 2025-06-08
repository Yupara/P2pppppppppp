from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)

    ads = relationship("Ad", back_populates="owner")
    orders_bought = relationship("Order", foreign_keys='Order.buyer_id', back_populates="buyer")
    orders_sold = relationship("Order", foreign_keys='Order.seller_id', back_populates="seller")


class AdType(str, enum.Enum):
    buy = "buy"
    sell = "sell"

class Ad(Base):
    __tablename__ = "ads"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(AdType))
    amount = Column(Float)
    price = Column(Float)
    currency = Column(String, default="USDT")
    created_at = Column(DateTime, default=datetime.utcnow)

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="ads")


class OrderStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    completed = "completed"
    dispute = "dispute"
    cancelled = "cancelled"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    price = Column(Float)
    status = Column(Enum(OrderStatus), default=OrderStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)

    buyer_id = Column(Integer, ForeignKey("users.id"))
    seller_id = Column(Integer, ForeignKey("users.id"))
    ad_id = Column(Integer, ForeignKey("ads.id"))

    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="orders_bought")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="orders_sold")
    ad = relationship("Ad")
