from sqlalchemy import Column, Integer, String, Float, ForeignKey
from database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)  # "buy" или "sell"
    amount = Column(Float)
    price = Column(Float)
    status = Column(String)  # например, "завершено", "в процессе"
