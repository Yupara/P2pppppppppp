from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UserCreate(BaseModel):
    username: str
    password: str
    referral_code: Optional[str]

class UserOut(BaseModel):
    id: int
    username: str
    balance: float
    commission_earned: float
    referrals_count: int
    is_verified: int

    class Config:
        orm_mode = True

class AdCreate(BaseModel):
    type: str
    crypto: str
    fiat: str
    amount: float
    price: float
    min_limit: float
    max_limit: float
    payment_methods: str

class AdOut(AdCreate):
    id: int
    user: UserOut
    created_at: str
    user_rating: float

    class Config:
        orm_mode = True

class OrderCreate(BaseModel):
    ad_id: int
    amount: float

class OrderOut(OrderCreate):
    id: int
    buyer: UserOut
    ad: AdOut
    status: str
    created_at: str

    class Config:
        orm_mode = True

class MessageCreate(BaseModel):
    order_id: int
    text: str

class MessageOut(BaseModel):
    sender: UserOut
    text: str
    timestamp: str

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    username: str
    password: str
    referrer_id: Optional[int] = None  # <- добавлено
