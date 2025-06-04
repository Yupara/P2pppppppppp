from fastapi import FastAPI, Request, Form, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from passlib.context import CryptContext
from aiosmtplib import SMTP
from datetime import datetime, timedelta
import jwt
import os
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройка базы данных SQLite
DATABASE_URL = "sqlite:///p2p_exchange.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Модели
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True)
    password = Column(String)
    referral_code = Column(String, unique=True)
    trades_completed = Column(Integer, default=0)
    balance = Column(Float, default=0.0)
    cancellations = Column(Integer, default=0)
    verified = Column(Boolean, default=False)
    passport_verified = Column(Boolean, default=False)
    blocked_until = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    verification_code = Column(String, nullable=True)
    referral_earnings = Column(Float, default=0.0)
    btc_balance = Column(Float, default=0.0)
    eth_balance = Column(Float, default=0.0)

class Offer(Base):
    __tablename__ = "offers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    offer_type = Column(String)  # "sell" или "buy"
    currency = Column(String)    # Криптовалюта (USDT, BTC, ETH)
    amount = Column(Float)       # Сумма в криптовалюте
    fiat = Column(String)        # Фиатная валюта (USD, RUB, EUR)
    fiat_amount = Column(Float)  # Сумма в фиате
    payment_method = Column(String)
    contact = Column(String)
    status = Column(String, default="active")
    buyer_id = Column(Integer, ForeignKey("users.id"))
    buyer_confirmed = Column(Boolean, default=False)
    seller_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    frozen_amount = Column(Float, default=0.0)
    user = relationship("User", foreign_keys=[user_id])
    buyer = relationship("User", foreign_keys=[buyer_id])

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    text = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", foreign_keys=[user_id])

class Dispute(Base):
    __tablename__ = "disputes"
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    screenshot = Column(String, nullable=True)
    video = Column(String, nullable=True)
    status = Column(String, default="open")
    resolution = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"))
    commission = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class AdminWithdrawal(Base):
    __tablename__ = "admin_withdrawals"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

# Хэширование паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка email
email_sender = SMTP(
    hostname="smtp.gmail.com",
    port=587,
    use_tls=False,
    start_tls=True,
    username=os.getenv("EMAIL_USER"),
    password=os.getenv("EMAIL_PASS")
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создание таблиц
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функция для конвертации крипты в USDT (заглушка для теста)
def convert_to_usdt(currency: str, amount: float) -> float:
    rates = {"USDT": 1.0, "BTC": 70000, "ETH": 3500}  # Примерные курсы
    return amount * rates.get(currency, 1.0)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "user_id": None})

@app.get("/offers")
async def get_offers(offer_type: str = None, currency: str = None, fiat: str = None, payment_method: str = None, amount: float = None):
    db = next(get_db())
    try:
        query = db.query(Offer).filter(Offer.status == "active")
        if offer_type:
            query = query.filter(Offer.offer_type == offer_type)
        if currency:
            query = query.filter(Offer.currency == currency)
        if fiat:
            query = query.filter(Offer.fiat == fiat)
        if payment_method and payment_method != "all":
            query = query.filter(Offer.payment_method == payment_method)
        if amount:
            query = query.filter(Offer.amount >= amount)
        offers = query.all()
        return [{
            "id": o.id,
            "user_id": o.user_id,
            "offer_type": o.offer_type,
            "currency": o.currency,
            "amount": o.amount,
            "fiat": o.fiat,
            "fiat_amount": o.fiat_amount,
            "payment_method": o.payment_method,
            "contact": o.contact,
            "status": o.status,
            "created_at": o.created_at
        } for o in offers]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/my-offers")
async def get_my_offers():
    db = next(get_db())
    try:
        offers = db.query(Offer).filter(Offer.status == "active").all()  # Показываем все активные офферы без авторизации
        return [{
            "id": o.id,
            "user_id": o.user_id,
            "offer_type": o.offer_type,
            "currency": o.currency,
            "amount": o.amount,
            "fiat": o.fiat,
            "fiat_amount": o.fiat_amount,
            "payment_method": o.payment_method,
            "contact": o.contact,
            "status": o.status,
            "created_at": o.created_at,
            "buyer_id": o.buyer_id,
            "frozen_amount": o.frozen_amount
        } for o in offers]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/admin-stats")
async def admin_stats():
    db = next(get_db())
    try:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        transactions = db.query(Transaction).filter(Transaction.created_at >= today).all()
        total_earnings_today = sum(t.commission for t in transactions)
        total_earnings = sum(t.commission for t in db.query(Transaction).all())
        withdrawals = sum(w.amount for w in db.query(AdminWithdrawal).all())
        available_earnings = total_earnings - withdrawals
        active_users = db.query(User).filter(User.verified == True, User.blocked_until == None).all()
        week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_transactions = db.query(Transaction).filter(Transaction.created_at >= week_ago).all()
        daily_stats = {i: 0 for i in range(7)}
        for t in weekly_transactions:
            day_index = (datetime.utcnow() - t.created_at).days
            if day_index < 7:
                daily_stats[day_index] += t.commission
        weekly_stats = [daily_stats[i] for i in range(6, -1, -1)]
        large_trades = db.query(Offer).filter(Offer.status == "completed").all()
        large_trades = [
            {"id": o.id, "fiat_amount": o.fiat_amount, "fiat": o.fiat, "created_at": o.created_at}
            for o in large_trades if o.fiat_amount * convert_to_usdt(o.currency, 1) >= 10000
        ]
        return {
            "earnings_today": total_earnings_today,
            "earnings_total": total_earnings,
            "available_earnings": available_earnings,
            "active_users": [{"id": u.id, "email": u.email, "trades_completed": u.trades_completed} for u in active_users],
            "weekly_stats": weekly_stats,
            "large_trades": large_trades
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
