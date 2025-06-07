from sqlalchemy import Column, Integer, Float, ForeignKey
from database import Base

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    ad_id = Column(Integer, ForeignKey("ads.id"))
    buyer_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
