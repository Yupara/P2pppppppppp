import os
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from sqlalchemy import (
    create_engine, Column, Integer, String,
    Float, ForeignKey, DateTime, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# — Админ UUID —
ADMIN_UUID = "293dd908-eac9-4082-b5e6-112d649a60bc"

# — Настройка БД —
DATABASE_URL = "sqlite:///./p2p.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# — Модели —
class Ad(Base):
    __tablename__ = "ads"
    id              = Column(Integer, primary_key=True, index=True)
    uuid            = Column(String, default=lambda: str(uuid4()), unique=True)
    type            = Column(String, nullable=False)  # buy/sell
    crypto          = Column(String, nullable=False)
    fiat            = Column(String, nullable=False)
    amount          = Column(Float, nullable=False)
    price           = Column(Float, nullable=False)
    min_limit       = Column(Float, nullable=False)
    max_limit       = Column(Float, nullable=False)
    payment_methods = Column(String, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)
    trades          = relationship("Trade", back_populates="ad")

class Trade(Base):
    __tablename__ = "trades"
    id         = Column(Integer, primary_key=True, index=True)
    ad_id      = Column(Integer, ForeignKey("ads.id"))
    buyer_uuid = Column(String, nullable=False)
    status     = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    ad         = relationship("Ad", back_populates="trades")
    messages   = relationship("Message", back_populates="trade", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id          = Column(Integer, primary_key=True, index=True)
    trade_id    = Column(Integer, ForeignKey("trades.id"))
    sender_uuid = Column(String, nullable=False)
    content     = Column(Text, nullable=False)
    timestamp   = Column(DateTime, default=datetime.utcnow)
    trade       = relationship("Trade", back_populates="messages")

Base.metadata.create_all(bind=engine)

# — FastAPI setup —
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY","secret123"))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# — Утилиты —
def get_user_uuid(request: Request):
    if not request.session.get("user_uuid"):
        request.session["user_uuid"] = str(uuid4())
    return request.session["user_uuid"]

def cancel_expired(db: Session):
    now = datetime.utcnow()
    for t in db.query(Trade).filter(Trade.status=="pending", Trade.expires_at<=now):
        t.status = "canceled"
    db.commit()

# — Маршруты —

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/market")

@app.get("/market", response_class=HTMLResponse)
def market(request: Request, db: Session = Depends(get_db)):
    cancel_expired(db)
    user_uuid = get_user_uuid(request)

    # фильтры из query params
    crypto  = request.query_params.get("crypto","")
    fiat    = request.query_params.get("fiat","")
    payment = request.query_params.get("payment","")

    query = db.query(Ad)
    if crypto:
        query = query.filter(Ad.crypto == crypto)
    if fiat:
        query = query.filter(Ad.fiat == fiat)
    if payment:
        query = query.filter(Ad.payment_methods.ilike(f"%{payment}%"))

    ads = query.all()

    # distinct для фильтров
    cryptos  = [row[0] for row in db.query(Ad.crypto).distinct()]
    fiats    = [row[0] for row in db.query(Ad.fiat).distinct()]
    payments = []
    for pm, in db.query(Ad.payment_methods).distinct():
        for p in pm.split(","):
            p = p.strip()
            if p and p not in payments:
                payments.append(p)

    return templates.TemplateResponse("market.html", {
        "request": request,
        "ads": ads,
        "user_uuid": user_uuid,
        "cryptos": cryptos,
        "fiats": fiats,
        "payments": payments,
        "current_crypto": crypto,
        "current_fiat": fiat,
        "current_payment": payment
    })

@app.get("/trade/create/{ad_id}")
def create_trade(ad_id: int, request: Request, db: Session = Depends(get_db)):
    cancel_expired(db)
    ad = db.query(Ad).get(ad_id)
    if not ad:
        raise HTTPException(404, "Ad not found")
    uu = get_user_uuid(request)
    trade = Trade(
        ad_id=ad.id,
        buyer_uuid=uu,
        status="pending",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )
    db.add(trade); db.commit(); db.refresh(trade)
    return RedirectResponse(f"/trade/{trade.id}", status_code=302)

@app.get("/trade/{trade_id}", response_class=HTMLResponse)
def view_trade(trade_id: int, request: Request, db: Session = Depends(get_db)):
    cancel_expired(db)
    trade = db.query(Trade).get(trade_id)
    if not trade:
        raise HTTPException(404, "Trade not found")
    uu = get_user_uuid(request)
    is_buyer  = (trade.buyer_uuid == uu)
    is_seller = (trade.ad.uuid == uu)
    if not (is_buyer or is_seller):
        raise HTTPException(403, "Access denied")
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "trade": trade,
        "messages": trade.messages,
        "is_buyer": is_buyer,
        "is_seller": is_seller,
        "now": datetime.utcnow().isoformat()
    })

@app.post("/trade/{trade_id}/message")
def send_message(trade_id: int, request: Request, content: str = Form(...), db: Session = Depends(get_db)):
    trade = db.query(Trade).get(trade_id)
    uu = get_user_uuid(request)
    if not trade or uu not in (trade.buyer_uuid, trade.ad.uuid):
        raise HTTPException(403, "Access denied")
    msg = Message(trade_id=trade_id, sender_uuid=uu, content=content, timestamp=datetime.utcnow())
    db.add(msg); db.commit()
    return RedirectResponse(f"/trade/{trade_id}", status_code=302)
