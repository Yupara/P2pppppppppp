from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class OrderCreate(BaseModel):
    crypto_currency: str
    fiat_currency: str
    amount: float
    price: float
    is_buy: bool

class OrderOut(BaseModel):
    id: int
    crypto_currency: str
    fiat_currency: str
    amount: float
    price: float
    is_buy: bool
    owner_id: int
    created_at: datetime

    class Config:
        orm_mode = True
