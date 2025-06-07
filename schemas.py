from pydantic import BaseModel
from enum import Enum

class OrderType(str, Enum):
    buy = "buy"
    sell = "sell"

class OrderStatus(str, Enum):
    pending = "ожидание"
    completed = "завершено"
    cancelled = "отменено"

class OrderOut(BaseModel):
    id: int
    type: OrderType
    amount: float
    price: float
    status: OrderStatus

    class Config:
        orm_mode = True
