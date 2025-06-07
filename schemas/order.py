from pydantic import BaseModel
from typing import Literal

class OrderCreate(BaseModel):
    type: Literal["buy", "sell"]
    amount: float
    price: float

class OrderOut(BaseModel):
    id: int
    type: str
    amount: float
    price: float
    status: str

    class Config:
        orm_mode = True
