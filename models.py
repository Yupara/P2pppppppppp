from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from .database import Base

class OrderType(str, enum.Enum):
    buy = "buy"
    sell = "sell"

class OrderStatus(str, enum.Enum):
    pending = "ожидание"
    completed = "завершено"
    cancelled = "отменено"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(Enum(OrderType))
    amount = Column(Float)
    price = Column(Float)
    status = Column(Enum(OrderStatus), default=OrderStatus.pending)

    user = relationship("User", back_populates="orders")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    orders = relationship("Order", back_populates="user")
