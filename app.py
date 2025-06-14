# app.py

import os
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import (
    FastAPI, Request, Form, Depends,
    HTTPException
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from sqlalchemy import (
    create_engine, Column, Integer,
    String, Float, ForeignKey,
    DateTime, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# --- Настройка БД ---
DATABASE_URL = "sqlite:///./p2p.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Модели ---
class Ad(Base):
    __tablename__ = "ads"
    id              = Column(Integer, primary_key=True, index=True)
    uuid            = Column(String, default=lambda: str(uuid4()), unique=True)
    type            = Column(String, nullable=False)  # "buy" или "sell"
    crypto          = Column(String, nullable=False)
    fiat            = Column(String, nullable=False)
    amount          = Column(Float, nullable=False)
    price           = Column(Float, nullable=False)
    min_limit       = Column(Float, nullable=False)
    max_limit       = Column(Float, nullable=False)
    payment_methods = Column(String, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)

    trades = relationship("Trade", back_populates="ad")

class Trade(Base):
    __tablename__ = "trades"
    id         = Column(Integer, primary_key=True, index=True)
    ad_id      = Column(Integer, ForeignKey("ads.id"))
    buyer_uuid = Column(String, nullable=False)  # session user id
    status     = Column(String, default="pending")  # pending, paid, confirmed, canceled, disputed
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # set = created_at + timedelta

    ad         = relationship("Ad", back_populates="trades")
    messages   = relationship("Message", back_populates="trade")

class Message(Base):
    __tablename__ = "messages"
    id        = Column(Integer, primary_key=True, index=True)
    trade_id  = Column(Integer, ForeignKey("trades.id"))
    sender    = Column(String, nullable=False)  # buyer_uuid or "seller"
    text      = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    trade     = relationship("Trade", back_populates="messages")

# создаём все таблицы
Base.metadata.create_all(bind=engine)

# --- FastAPI ---
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY","secret123"))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Утилита: получаем уникальный идентификатор пользователя из сессии ---
def get_user_uuid(request: Request):
    if not request.session.get("user_uuid"):
        request.session["user_uuid"] = str(uuid4())
    return request.session["user_uuid"]

# --- Таймер отмены сделок: при каждом заходе проверяем и снимаем просроченные ---
def cancel_expired(db: Session):
    now = datetime.utcnow()
    expired = db.query(Trade).filter(
        Trade.status=="pending",
        Trade.expires_at <= now
    ).all()
    for t in expired:
        t.status = "canceled"
    db.commit()

# --- Маршруты ---

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/market")

@app.get("/market", response_class=HTMLResponse)
def market(request: Request, db: Session = Depends(get_db)):
    # отменяем просроченные
    cancel_expired(db)

    user_uuid = get_user_uuid(request)
    ads = db.query(Ad).all()
    return templates.TemplateResponse("market.html", {
        "request": request,
        "ads": ads,
        "user_uuid": user_uuid
    })

@app.get("/create_ad", response_class=HTMLResponse)
def create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create_ad")
def create_ad(
    request: Request,
    type: str = Form(...),
    crypto: str = Form(...),
    fiat: str = Form(...),
    amount: float = Form(...),
    price: float = Form(...),
    min_limit: float = Form(...),
    max_limit: float = Form(...),
    payment_methods: str = Form(...),
    db: Session = Depends(get_db)
):
    ad = Ad(
        type=type, crypto=crypto, fiat=fiat,
        amount=amount, price=price,
        min_limit=min_limit, max_limit=max_limit,
        payment_methods=payment_methods,
        created_at=datetime.utcnow()
    )
    db.add(ad); db.commit()
    return RedirectResponse("/market", status_code=302)

@app.get("/trade/create/{ad_id}")
def create_trade(ad_id: int, request: Request, db: Session = Depends(get_db)):
    cancel_expired(db)
    ad = db.query(Ad).get(ad_id)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    user_uuid = get_user_uuid(request)
    # нельзя самому себе: сопоставим seller uuid == ad.uuid?
    trade = Trade(
        ad_id=ad.id,
        buyer_uuid=user_uuid,
        status="pending",
        created_at=datetime.utcnow()
    )
    trade.expires_at = trade.created_at + timedelta(minutes=30)
    db.add(trade); db.commit(); db.refresh(trade)
    return RedirectResponse(f"/trade/{trade.id}", status_code=302)

@app.get("/trade/{trade_id}", response_class=HTMLResponse)
def view_trade(trade_id: int, request: Request, db: Session = Depends(get_db)):
    cancel_expired(db)
    trade = db.query(Trade).get(trade_id)
    if not trade:
        raise HTTPException(404, "Сделка не найдена")
    user_uuid = get_user_uuid(request)
    # seller_uuid = trade.ad.uuid
    is_buyer  = (trade.buyer_uuid == user_uuid)
    is_seller = (trade.ad.uuid    == user_uuid)
    if not (is_buyer or is_seller):
        raise HTTPException(403, "Нет доступа к этой сделке")
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "trade": trade,
        "is_buyer": is_buyer,
        "is_seller": is_seller,
        "now": datetime.utcnow().isoformat()
    })

@app.post("/trade/{trade_id}/paid")
def mark_paid(trade_id: int, request: Request, db: Session = Depends(get_db)):
    trade = db.query(Trade).get(trade_id)
    user_uuid = get_user_uuid(request)
    if trade.buyer_uuid != user_uuid or trade.status!="pending":
        raise HTTPException(403)
    trade.status = "paid"
    db.commit()
    return RedirectResponse(f"/trade/{trade_id}", status_code=302)

@app.post("/trade/{trade_id}/confirm")
def mark_confirm(trade_id: int, request: Request, db: Session = Depends(get_db)):
    trade = db.query(Trade).get(trade_id)
    user_uuid = get_user_uuid(request)
    if trade.ad.uuid != user_uuid or trade.status!="paid":
        raise HTTPException(403)
    trade.status = "confirmed"
    db.commit()
    return RedirectResponse(f"/trade/{trade_id}", status_code=302)

@app.post("/trade/{trade_id}/dispute")
def mark_dispute(trade_id: int, request: Request, db: Session = Depends(get_db)):
    trade = db.query(Trade).get(trade_id)
    user_uuid = get_user_uuid(request)
    if user_uuid not in (trade.buyer_uuid, trade.ad.uuid):
        raise HTTPException(403)
    trade.status = "disputed"
    db.commit()
    return RedirectResponse(f"/trade/{trade_id}", status_code=302)

@app.post("/trade/{trade_id}/message")
def send_message(
    trade_id: int,
    request: Request,
    text: str = Form(...),
    db: Session = Depends(get_db)
):
    trade = db.query(Trade).get(trade_id)
    user_uuid = get_user_uuid(request)
    if user_uuid not in (trade.buyer_uuid, trade.ad.uuid):
        raise HTTPException(403)
    msg = Message(
        trade_id=trade.id,
        sender=user_uuid,
        text=text,
        timestamp=datetime.utcnow()
    )
    db.add(msg); db.commit()
    return RedirectResponse(f"/trade/{trade_id}", status_code=302)

# в app.py

from typing import Optional

@app.get("/market")
def market(
    request: Request,
    crypto: Optional[str] = None,
    fiat: Optional[str] = None,
    payment: Optional[str] = None,
    db: Session = Depends(get_db)
):
    cancel_expired(db)
    user_uuid = get_user_uuid(request)
    query = db.query(Ad)

    if crypto:
        query = query.filter(Ad.crypto == crypto)
    if fiat:
        query = query.filter(Ad.fiat == fiat)
    if payment:
        # проверяем, что заданный метод есть в CSV-списке payment_methods
        query = query.filter(Ad.payment_methods.ilike(f"%{payment}%"))

    ads = query.all()
    # Для выпадающих списков передаём возможные варианты:
    cryptos = [row[0] for row in db.query(Ad.crypto).distinct()]
    fiats   = [row[0] for row in db.query(Ad.fiat).distinct()]
    payments = set()
    for pm in db.query(Ad.payment_methods).distinct():
        for p in pm[0].split(","):
            payments.add(p.strip())
    return templates.TemplateResponse("market.html", {
        "request": request,
        "ads": ads,
        "user_uuid": user_uuid,
        "cryptos": cryptos,
        "fiats": fiats,
        "payments": sorted(payments),
        "current_crypto": crypto or "",
        "current_fiat": fiat or "",
        "current_payment": payment or ""
    })
