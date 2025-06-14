from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timedelta

from app import get_db, get_user_uuid, templates, Ad, Trade

router = APIRouter(prefix="/orders")

# Список всех криптовалют и фиатов
CRYPTOS = ["USDT", "BTC", "ETH"]
FIATS = [
    "USD","EUR","GBP","RUB","UAH","KZT","TRY","AED","NGN","INR","VND",
    "BRL","ARS","COP","PEN","MXN","CLP","ZAR","EGP","GHS","KES","MAD",
    "PKR","BDT","LKR","IDR","THB","MYR","PHP","KRW","TJS"
]
# Пример P2P-способов оплаты (Bybit-стиль)
PAYMENTS = [
    "Сбербанк","Тинькофф","Альфа-банк","ВТБ","Газпромбанк",
    "PayPal","Wise","Revolut","Qiwi","Yandex.Money","Monobank"
]

@router.get("/create/{ad_id}", response_class=HTMLResponse)
def show_create_order(ad_id: int, request: Request, db: Session = Depends(get_db)):
    ad = db.query(Ad).get(ad_id)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    user_uuid = get_user_uuid(request)
    if ad.uuid == user_uuid:
        raise HTTPException(400, "Нельзя купить своё объявление")
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "order": None,
        "messages": [],
        "cryptos": CRYPTOS,
        "fiats": FIATS,
        "payments": PAYMENTS
    })

@router.post("/create/{ad_id}")
def create_order(
    ad_id: int,
    request: Request,
    crypto: str = Form(...),
    fiat: str = Form(...),
    amount: float = Form(...),
    payment_method: str = Form(...),
    db: Session = Depends(get_db)
):
    ad = db.query(Ad).get(ad_id)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    user_uuid = get_user_uuid(request)
    trade = Trade(
        ad_id=ad.id,
        buyer_uuid=user_uuid,
        status="pending",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )
    db.add(trade)
    db.commit()
    return RedirectResponse(f"/trade/{trade.id}", status_code=302)

@router.get("/mine", response_class=HTMLResponse)
def my_orders(request: Request, db: Session = Depends(get_db)):
    user_uuid = get_user_uuid(request)
    orders = db.query(Trade).filter(
        (Trade.buyer_uuid == user_uuid) | (Trade.ad.has(uuid=user_uuid))
    ).all()
    return templates.TemplateResponse("orders.html", {
        "request": request,
        "orders": orders
    })
