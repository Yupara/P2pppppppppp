from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import uuid

app = FastAPI()

# Разрешаем запросы с React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Ad(BaseModel):
    id: str
    user: str
    type: str  # buy or sell
    coin: str
    price: float
    available: float
    limits: str
    payment_methods: List[str]

class Deal(BaseModel):
    id: str
    ad_id: str
    user: str
    amount: float
    status: str  # created, paid, completed

# Временное хранилище объявлений и сделок
ads_db = [
    Ad(id="ad1", user="Seller1", type="sell", coin="USDT", price=70.96, available=300, limits="500-500000 RUB", payment_methods=["SBP", "Bank Transfer"]),
    Ad(id="ad2", user="Seller2", type="sell", coin="USDT", price=71.03, available=120, limits="500-500000 RUB", payment_methods=["SBP"]),
    Ad(id="ad3", user="Buyer1", type="buy", coin="USDT", price=70.50, available=200, limits="500-500000 RUB", payment_methods=["Bank Transfer"]),
]

deals_db = []

@app.get("/ads", response_model=List[Ad])
def get_ads(type: Optional[str] = None):
    if type:
        return [ad for ad in ads_db if ad.type == type]
    return ads_db

class DealCreateRequest(BaseModel):
    ad_id: str
    user: str
    amount: float

@app.post("/deals", response_model=Deal)
def create_deal(deal_req: DealCreateRequest):
    # Проверяем что объявление существует и доступно
    ad = next((a for a in ads_db if a.id == deal_req.ad_id), None)
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    if deal_req.amount > ad.available:
        raise HTTPException(status_code=400, detail="Amount exceeds available")

    deal_id = str(uuid.uuid4())
    deal = Deal(
        id=deal_id,
        ad_id=ad.id,
        user=deal_req.user,
        amount=deal_req.amount,
        status="created"
    )
    deals_db.append(deal)
    # уменьшаем доступное количество в объявлении
    ad.available -= deal_req.amount
    return deal

@app.get("/deals/{deal_id}", response_model=Deal)
def get_deal(deal_id: str):
    deal = next((d for d in deals_db if d.id == deal_id), None)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
