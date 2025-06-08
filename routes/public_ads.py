from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from uuid import uuid4

router = APIRouter()

# Фейковая база объявлений
ads_db = []

class PublicAd(BaseModel):
    id: str
    type: str  # "buy" или "sell"
    price: float
    amount: float
    currency: str
    nickname: str

# Получить список всех объявлений
@router.get("/api/public_ads", response_model=List[PublicAd])
def get_ads():
    return ads_db

# Добавить фейковые объявления (для теста)
@router.post("/api/public_ads/fake")
def create_fake_ads():
    ads_db.clear()
    ads_db.append(PublicAd(
        id=str(uuid4()),
        type="buy",
        price=89500,
        amount=1000,
        currency="RUB",
        nickname="CryptoKing"
    ))
    ads_db.append(PublicAd(
        id=str(uuid4()),
        type="sell",
        price=90500,
        amount=750,
        currency="RUB",
        nickname="USDT_Pro"
    ))
    return {"detail": "Фейковые объявления созданы"}
