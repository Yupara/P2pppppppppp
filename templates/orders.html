from datetime import datetime, timedelta
from fastapi import (
    APIRouter, Depends, HTTPException, Request,
    Form, UploadFile, File
)
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from uuid import uuid4
import os, shutil

from app import get_db, get_user_uuid, templates
from app import User, Ad, Trade, Message  # модели из app.py

router = APIRouter()

# --- константы ---
CRYPTO_LIST = ["USDT","BTC","ETH","TRUMP"]
FIAT_LIST = [
    "USD","EUR","GBP","RUB","UAH","KZT","TRY","AED","NGN","INR",
    "VND","BRL","ARS","COP","PEN","MXN","CLP","ZAR","EGP","GHS",
    "KES","MAD","PKR","BDT","LKR","IDR","THB","MYR","PHP","KRW","TJS"
]
PAYMENT_METHODS = [
    "SBP","Bank Transfer","Visa/Mastercard","PayPal","PerfectMoney",
    "Qiwi","YooMoney","WesternUnion","MoneyGram","SWIFT"
]

# --- создать заказ (покупка) ---
@router.post("/orders/create/{ad_id}")
def create_order(ad_id: int, request: Request, db: Session = Depends(get_db)):
    # пользователь
    user_uuid = get_user_uuid(request)
    ad = db.query(Ad).get(ad_id)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    if ad.user_uuid == user_uuid:
        raise HTTPException(400, "Нельзя купить у себя")

    # создаём сделку
    trade = Trade(
        ad_id=ad.id,
        buyer_uuid=user_uuid,
        amount=ad.amount,
        fiat=ad.fiat,
        crypto=ad.crypto,
        payment_method=ad.payment_methods,
        status="pending",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        escrow_amount=ad.amount  # удерживаем всю сумму в эскроу
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return RedirectResponse(f"/trade/{trade.id}", status_code=302)

# --- страница сделки ---
@router.get("/trade/{trade_id}", response_class=HTMLResponse)
def trade_view(trade_id: int, request: Request, db: Session = Depends(get_db)):
    trade = db.query(Trade).get(trade_id)
    if not trade:
        raise HTTPException(404, "Сделка не найдена")
    user_uuid = get_user_uuid(request)
    # проверяем доступ
    if user_uuid not in (trade.buyer_uuid, trade.ad.user_uuid):
        raise HTTPException(403, "Нет доступа")
    # соберём чат
    messages = db.query(Message).filter(Message.trade_id==trade.id).order_by(Message.timestamp).all()
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "trade": trade,
        "messages": messages,
        "is_buyer": user_uuid==trade.buyer_uuid,
        "is_seller": user_uuid==trade.ad.user_uuid,
        "cryptos": CRYPTO_LIST,
        "fiats": FIAT_LIST,
        "payments": PAYMENT_METHODS
    })

# --- отметка «Я оплатил» ---
@router.post("/trade/{trade_id}/pay")
def pay_order(trade_id: int, request: Request, db: Session = Depends(get_db)):
    trade = db.query(Trade).get(trade_id)
    if trade.status != "pending":
        raise HTTPException(400, "Невозможно оплатить")
    user_uuid = get_user_uuid(request)
    if user_uuid != trade.buyer_uuid:
        raise HTTPException(403, "Только покупатель")
    # переходим в эскроу
    trade.status = "paid"
    db.commit()
    return RedirectResponse(f"/trade/{trade.id}", 302)

# --- отметка «Подтвердить получение» ---
@router.post("/trade/{trade_id}/confirm")
def confirm_order(trade_id: int, request: Request, db: Session = Depends(get_db)):
    trade = db.query(Trade).get(trade_id)
    if trade.status != "paid":
        raise HTTPException(400, "Невозможно подтвердить")
    user_uuid = get_user_uuid(request)
    if user_uuid != trade.ad.user_uuid:
        raise HTTPException(403, "Только продавец")
    # распределяем эскроу: комиссия 1% (0.5% с каждой стороны)
    commission = trade.escrow_amount * 0.01
    net = trade.escrow_amount - commission
    seller = db.query(User).filter(User.uuid==trade.ad.user_uuid).first()
    buyer  = db.query(User).filter(User.uuid==trade.buyer_uuid).first()
    # апдейтим балансы
    seller.balance += net
    # buyer баланс зачислять его крипту отдельно
    trade.status = "confirmed"
    db.commit()
    return RedirectResponse(f"/trade/{trade.id}", 302)

# --- открыть спор ---
@router.post("/trade/{trade_id}/dispute")
def dispute_order(trade_id: int, request: Request, db: Session = Depends(get_db)):
    trade = db.query(Trade).get(trade_id)
    if trade.status not in ("pending","paid"):
        raise HTTPException(400, "Невозможно в спор")
    user_uuid = get_user_uuid(request)
    if user_uuid not in (trade.buyer_uuid, trade.ad.user_uuid):
        raise HTTPException(403, "Нет доступа")
    trade.status = "disputed"
    db.commit()
    return RedirectResponse(f"/trade/{trade.id}", 302)

# --- чат с фото ---
@router.post("/trade/{trade_id}/message")
def send_message(
    trade_id: int,
    request: Request,
    text: str = Form(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    trade = db.query(Trade).get(trade_id)
    user_uuid = get_user_uuid(request)
    if user_uuid not in (trade.buyer_uuid, trade.ad.user_uuid):
        raise HTTPException(403, "Нет доступа")

    msg = Message(
        trade_id=trade_id,
        sender_uuid=user_uuid,
        content=text or "",
        timestamp=datetime.utcnow()
    )
    db.add(msg)
    db.commit()
    # сохраняем файл
    if file:
        os.makedirs("static/uploads", exist_ok=True)
        path = f"static/uploads/{uuid4().hex}_{file.filename}"
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        # привяжем ссылку к сообщению
        msg.file_path = path
        db.commit()
    return RedirectResponse(f"/trade/{trade_id}", 302)
