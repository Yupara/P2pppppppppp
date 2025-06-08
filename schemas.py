from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# --- Пользователь ---

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(UserBase):
    id: int
    email: EmailStr

    class Config:
        orm_mode = True

# --- Токены ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- Объявления (Buy/Sell Offers) ---

class AdBase(BaseModel):
    type: str  # "buy" или "sell"
    price: float
    amount: float
    currency: str
    payment_method: str
    min_limit: float
    max_limit: float

class AdCreate(AdBase):
    pass

class AdOut(AdBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        orm_mode = True

# --- Сделка (Trade) ---

class TradeBase(BaseModel):
    ad_id: int
    amount: float

class TradeCreate(TradeBase):
    pass

class TradeOut(BaseModel):
    id: int
    buyer_id: int
    seller_id: int
    ad_id: int
    amount: float
    price: float
    status: str
    created_at: datetime

    class Config:
        orm_mode = True

# --- Сообщения в сделке ---

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass

class MessageOut(BaseModel):
    id: int
    trade_id: int
    sender_id: int
    content: str
    timestamp: datetime

    class Config:
        orm_mode = True
