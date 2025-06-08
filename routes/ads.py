from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from uuid import uuid4
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()

ads = []

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Просто пример "получения пользователя по токену"
def get_current_user(token: str = Depends(oauth2_scheme)):
    # В реальности проверяй JWT
    return {"username": "demo_user"}

class AdCreate(BaseModel):
    type: str  # "buy" или "sell"
    price: float
    amount: float
    currency: str

class Ad(BaseModel):
    id: str
    type: str
    price: float
    amount: float
    currency: str
    owner: str

@router.post("/api/ads/create")
def create_ad(ad: AdCreate, user: dict = Depends(get_current_user)):
    new_ad = Ad(
        id=str(uuid4()),
        type=ad.type,
        price=ad.price,
        amount=ad.amount,
        currency=ad.currency.upper(),
        owner=user['username']
    )
    ads.append(new_ad)
    return {"detail": "Объявление создано"}

@router.get("/api/public_ads", response_model=List[Ad])
def get_public_ads():
    return ads
