from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4

router = APIRouter()

ads_db = []

class PublicAd(BaseModel):
    id: str
    type: str  # "buy" или "sell"
    price: float
    amount: float
    currency: str
    nickname: str

@router.get("/api/public_ads", response_model=List[PublicAd])
def get_ads(
    type: Optional[str] = Query(None, regex="^(buy|sell)$"),
    currency: Optional[str] = None
):
    result = ads_db
    if type:
        result = [ad for ad in result if ad.type == type]
    if currency:
        result = [ad for ad in result if ad.currency == currency.upper()]
    return result

@router.post("/api/public_ads/fake")
def create_fake_ads():
    ads_db.clear()
    ads_db.extend([
        PublicAd(id=str(uuid4()), type="buy", price=89500, amount=1000, currency="RUB", nickname="CryptoKing"),
        PublicAd(id=str(uuid4()), type="sell", price=90500, amount=750, currency="RUB", nickname="USDT_Pro"),
        PublicAd(id=str(uuid4()), type="buy", price=89000, amount=1500, currency="USD", nickname="FastBuyer"),
        PublicAd(id=str(uuid4()), type="sell", price=91000, amount=800, currency="USD", nickname="TrustTrader"),
    ])
    return {"detail": "Фейковые объявления обновлены"}
