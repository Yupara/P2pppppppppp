from pydantic import BaseModel
from enum import Enum

class OrderStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    completed = "completed"
    cancelled = "cancelled"

class OrderType(str, Enum):
    buy = "buy"
    sell = "sell"

class OrderCreate(BaseModel):
    ad_id: int
    amount: float
    price: float
    type: OrderType

class OrderOut(BaseModel):
    id: int
    ad_id: int
    amount: float
    price: float
    type: OrderType
    status: OrderStatus

    class Config:
        orm_mode = True
