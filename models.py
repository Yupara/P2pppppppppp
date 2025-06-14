# models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    ads = relationship("Ad", back_populates="user")
# В User
trades = relationship("Trade", back_populates="buyer")

class Ad(Base):
    __tablename__ = "ads"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)
    crypto = Column(String)
    fiat = Column(String)
    amount = Column(Float)
    price = Column(Float)
    min_limit = Column(Float)
    max_limit = Column(Float)
    payment_methods = Column(String)
    user_rating = Column(Float)
    
    user = relationship("User", back_populates="ads")

# В Ad
trades = relationship("Trade", back_populates="ad")
class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    ad_id = Column(Integer, ForeignKey("ads.id"))
    amount = Column(Float)
    status = Column(String, default="pending")  # pending, paid, completed, disputed
    created_at = Column(DateTime, default=datetime.utcnow)

    buyer = relationship("User", back_populates="trades")
    ad = relationship("Ad", back_populates="trades")
