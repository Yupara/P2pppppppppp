from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid
import pytz
import os

app = FastAPI()
engine = create_engine("sqlite:///p2p_exchange.db")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Модели базы данных
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    phone = Column(String, unique=True)
    passport_verified = Column(Boolean, default=False)
    balance_usdt = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    cancels = Column(Integer, default=0)
    is_blocked = Column(Boolean, default=False)
    blocked_until = Column(DateTime, nullable=True)
    referral_code = Column(String, unique=True)
    referral_earnings = Column(Float, default=0.0)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    referrer = relationship("User", remote_side=[id])

class Offer(Base):
    __tablename__ = "offers"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)  # "sell" или "buy"
    amount = Column(Float)
    fiat = Column(String)
    crypto = Column(String)
    payment_method = Column(String)
    rate = Column(Float)
    status = Column(String, default="open")
    user = relationship("User")

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True)
    offer_id = Column(Integer, ForeignKey("offers.id"))
    buyer_id = Column(Integer, ForeignKey("users.id"))
    seller_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    fiat = Column(String)
    crypto = Column(String)
    payment_method = Column(String)
    rate = Column(Float)
    status = Column(String, default="pending")
    dispute = Column(Boolean, default=False)
    frozen_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC))
    offer = relationship("Offer")
    buyer = relationship("User", foreign_keys=[buyer_id])
    seller = relationship("User", foreign_keys=[seller_id])

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    trade_id = Column(Integer, ForeignKey("trades.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(pytz.UTC))
    trade = relationship("Trade")
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    status = Column(String, default="open")
    response = Column(String, nullable=True)
    user = relationship("User")

class Dispute(Base):
    __tablename__ = "disputes"
    id = Column(Integer, primary_key=True)
    trade_id = Column(Integer, ForeignKey("trades.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    evidence = Column(String, nullable=True)  # Ссылка на скриншот/видео
    trade = relationship("Trade")
    user = relationship("User")

class Platform(Base):
    __tablename__ = "platform"
    id = Column(Integer, primary_key=True)
    earnings = Column(Float, default=0.0)

Base.metadata.create_all(engine)

# Pydantic модели для валидации
class UserCreate(BaseModel):
    username: str
    email: str
    phone: str
    referral_code: str = None

class OfferCreate(BaseModel):
    type: str
    amount: float
    fiat: str
    crypto: str
    payment_method: str
    rate: float

class TradeCreate(BaseModel):
    offer_id: int

class MessageCreate(BaseModel):
    trade_id: int
    receiver_id: int
    message: str

class SupportTicketCreate(BaseModel):
    message: str

class DisputeCreate(BaseModel):
    trade_id: int
    evidence: str = None

# Зависимость для сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Проверка блокировки пользователя
def check_blocked(user):
    if user.is_blocked and user.blocked_until and datetime.now(pytz.UTC) < user.blocked_until:
        raise HTTPException(status_code=403, detail="User is blocked")

# Регистрация пользователя
@app.post("/register/")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter((User.username == user.username) | (User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    referral_code = str(uuid.uuid4())[:8]
    new_user = User(username=user.username, email=user.email, phone=user.phone, referral_code=referral_code)
    if user.referral_code:
        referrer = db.query(User).filter(User.referral_code == user.referral_code).first()
        if referrer:
            new_user.referrer_id = referrer.id
    db.add(new_user)
    db.commit()
    return {"message": "Registration successful, awaiting passport verification", "referral_code": referral_code}

# Верификация паспорта (админ)
@app.post("/verify_passport/{user_id}")
def verify_passport(user_id: int, admin_id: int, db: Session = Depends(get_db)):
    if admin_id != 1:  # Админ — пользователь с id=1
        raise HTTPException(status_code=403, detail="Not authorized")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.passport_verified = True
    db.commit()
    return {"message": "User verified"}

# Создание объявления
@app.post("/create_offer/")
def create_offer(offer: OfferCreate, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.passport_verified:
        raise HTTPException(status_code=403, detail="User not verified")
    check_blocked(user)
    db_offer = Offer(user_id=user_id, type=offer.type, amount=offer.amount, fiat=offer.fiat, crypto=offer.crypto, payment_method=offer.payment_method, rate=offer.rate)
    db.add(db_offer)
    db.commit()
    return {"message": "Offer created", "offer_id": db_offer.id}

# Инициирование сделки
@app.post("/initiate_trade/{offer_id}")
def initiate_trade(offer_id: int, buyer_id: int, db: Session = Depends(get_db)):
    offer = db.query(Offer).filter(Offer.id == offer_id, Offer.status == "open").first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found or closed")
    buyer = db.query(User).filter(User.id == buyer_id).first()
    seller = db.query(User).filter(User.id == offer.user_id).first()
    check_blocked(buyer)
    check_blocked(seller)
    if offer.type == "sell":
        if seller.balance_usdt < offer.amount:
            raise HTTPException(status_code=400, detail="Seller has insufficient balance")
        seller.balance_usdt -= offer.amount
    db_trade = Trade(offer_id=offer_id, buyer_id=buyer_id, seller_id=offer.user_id, amount=offer.amount, fiat=offer.fiat, crypto=offer.crypto, payment_method=offer.payment_method, rate=offer.rate, frozen_amount=offer.amount if offer.type == "sell" else 0)
    db.add(db_trade)
    offer.status = "closed"
    db.commit()
    return {"message": "Trade initiated", "trade_id": db_trade.id}

# Отметка об оплате
@app.post("/mark_paid/{trade_id}")
def mark_paid(trade_id: int, buyer_id: int, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.buyer_id == buyer_id, Trade.status == "pending").first()
    if not trade:
        raise HTTPException(status_code=400, detail="Invalid trade")
    trade.status = "paid"
    db.commit()
    return {"message": "Payment marked, awaiting release"}

# Выпуск средств
@app.post("/release_funds/{trade_id}")
def release_funds(trade_id: int, seller_id: int, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.seller_id == seller_id, Trade.status == "paid").first()
    if not trade:
        raise HTTPException(status_code=400, detail="Invalid trade")
    buyer = db.query(User).filter(User.id == trade.buyer_id).first()
    seller = db.query(User).filter(User.id == trade.seller_id).first()
    buyer_rate = 0.005 if buyer.total_trades < 50 else 0.0025
    seller_rate = 0.005 if seller.total_trades < 50 else 0.0025
    buyer_commission = trade.amount * buyer_rate
    seller_commission = trade.amount * seller_rate
    amount_to_buyer = trade.amount - buyer_commission
    buyer.balance_usdt += amount_to_buyer
    trade.status = "completed"
    trade.frozen_amount = 0
    buyer.total_trades += 1
    seller.total_trades += 1
    platform = db.query(Platform).first()
    if not platform:
        platform = Platform(earnings=0.0)
        db.add(platform)
    platform.earnings += buyer_commission + seller_commission
    if buyer.referrer_id:
        referrer = db.query(User).filter(User.id == buyer.referrer_id).first()
        referrer.referral_earnings += buyer_commission * 0.2
    if seller.referrer_id:
        referrer = db.query(User).filter(User.id == seller.referrer_id).first()
        referrer.referral_earnings += seller_commission * 0.2
    db.commit()
    if trade.amount >= 10000:
        return {"message": "Trade completed, large trade (≥10,000 USDT)"}
    return {"message": "Trade completed"}

# Открытие спора
@app.post("/dispute/")
def dispute(dispute: DisputeCreate, user_id: int, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == dispute.trade_id).first()
    if not trade or trade.status not in ["pending", "paid"] or (trade.buyer_id != user_id and trade.seller_id != user_id):
        raise HTTPException(status_code=400, detail="Invalid trade")
    trade.dispute = True
    db_dispute = Dispute(trade_id=dispute.trade_id, user_id=user_id, evidence=dispute.evidence)
    db.add(db_dispute)
    db.commit()
    return {"message": "Dispute opened, funds frozen, admin notified"}

# Разрешение спора (админ)
@app.post("/resolve_dispute/{dispute_id}")
def resolve_dispute(dispute_id: int, admin_id: int, resolution: str, db: Session = Depends(get_db)):
    if admin_id != 1:
        raise HTTPException(status_code=403, detail="Not authorized")
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=400, detail="Dispute not found")
    trade = dispute.trade
    if resolution == "release":
        buyer = db.query(User).filter(User.id == trade.buyer_id).first()
        commission_rate = 0.005 if buyer.total_trades < 50 else 0.0025
        commission = trade.amount * commission_rate
        buyer.balance_usdt += trade.amount - commission
        platform = db.query(Platform).first()
        platform.earnings += commission
        trade.status = "completed"
    elif resolution == "refund":
        seller = db.query(User).filter(User.id == trade.seller_id).first()
        seller.balance_usdt += trade.frozen_amount
        trade.status = "cancelled"
    else:
        raise HTTPException(status_code=400, detail="Invalid resolution")
    trade.dispute = False
    trade.frozen_amount = 0
    db.commit()
    return {"message": f"Dispute resolved: {resolution}"}

# Отмена сделки
@app.post("/cancel_trade/{trade_id}")
def cancel_trade(trade_id: int, user_id: int, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.status == "pending").first()
    if not trade or (trade.buyer_id != user_id and trade.seller_id != user_id):
        raise HTTPException(status_code=400, detail="Invalid trade")
    user = db.query(User).filter(User.id == user_id).first()
    user.cancels += 1
    if user.cancels >= 10:
        user.is_blocked = True
        user.blocked_until = datetime.now(pytz.UTC) + timedelta(hours=24)
    if trade.frozen_amount > 0:
        seller = db.query(User).filter(User.id == trade.seller_id).first()
        seller.balance_usdt += trade.frozen_amount
    trade.status = "cancelled"
    trade.frozen_amount = 0
    db.commit()
    return {"message": "Trade cancelled"}

# Поддержка
@app.post("/support/")
def support(ticket: SupportTicketCreate, user_id: int, db: Session = Depends(get_db)):
    db_ticket = SupportTicket(user_id=user_id, message=ticket.message)
    db.add(db_ticket)
    db.commit()
    if "operator" in ticket.message.lower():
        return {"message": "Operator notified, please wait for response"}
    return {"message": "Support bot: How can I help you?"}

# WebSocket для чата
active_connections = {}

@app.websocket("/ws/trade/{trade_id}")
async def websocket_endpoint(websocket: WebSocket, trade_id: int):
    await websocket.accept()
    trade = SessionLocal().query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        await websocket.close()
        return
    user_ids = [trade.buyer_id, trade.seller_id]
    for user_id in user_ids:
        if user_id not in active_connections:
            active_connections[user_id] = []
        active_connections[user_id].append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            db = SessionLocal()
            message = Message(trade_id=trade_id, sender_id=data["sender_id"], receiver_id=data["receiver_id"], message=data["message"])
            db.add(message)
            db.commit()
            db.close()
            if data["receiver_id"] in active_connections:
                for conn in active_connections[data["receiver_id"]]:
                    await conn.send_json({"sender_id": data["sender_id"], "message": data["message"]})
    except WebSocketDisconnect:
        for user_id in user_ids:
            if websocket in active_connections.get(user_id, []):
                active_connections[user_id].remove(websocket)

# Личный кабинет пользователя
@app.get("/user/cabinet")
def user_cabinet(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    check_blocked(user)
    return {
        "balance": user.balance_usdt,
        "total_trades": user.total_trades,
        "referral_earnings": user.referral_earnings,
        "cancels": user.cancels,
        "is_blocked": user.is_blocked
    }

# Вывод средств
@app.post("/withdraw/")
def withdraw(user_id: int, amount: float, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    check_blocked(user)
    if user.balance_usdt < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    user.balance_usdt -= amount
    db.commit()
    return {"message": f"Withdrawal of {amount} USDT successful"}

# Админ-панель: просмотр заработка
@app.get("/admin/earnings")
def admin_earnings(admin_id: int, db: Session = Depends(get_db)):
    if admin_id != 1:
        raise HTTPException(status_code=403, detail="Not authorized")
    platform = db.query(Platform).first()
    return {"total_earnings": platform.earnings if platform else 0.0}

# Админ-панель: управление пользователями
@app.post("/admin/block_user/{user_id}")
def block_user(user_id: int, admin_id: int, db: Session = Depends(get_db)):
    if admin_id != 1:
        raise HTTPException(status_code=403, detail="Not authorized")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_blocked = True
    user.blocked_until = datetime.now(pytz.UTC) + timedelta(hours=24)
    db.commit()
    return {"message": "User blocked"}

# Шаблоны
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Главная страница
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, lang: str = "ru", db: Session = Depends(get_db)):
    offers = db.query(Offer).filter(Offer.status == "open").all()
    translations = {
        "ru": {"title": "P2P Обменник", "offers": "Доступные объявления"},
        "en": {"title": "P2P Exchange", "offers": "Available Offers"}
    }
    lang = lang if lang in translations else "ru"
    return templates.TemplateResponse("index.html", {"request": request, "offers": offers, "translations": translations[lang]})
