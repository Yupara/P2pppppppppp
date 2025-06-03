from fastapi import FastAPI, Request, Form, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from passlib.context import CryptContext
from twilio.rest import Client
from aiosmtplib import SMTP
from datetime import datetime, timedelta
import jwt
import os
from fastapi.middleware.cors import CORSMiddleware
import schedule
import time
import threading
from email.mime.text import MIMEText
import asyncio

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройка базы данных
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
    passport_file = Column(String, nullable=True)
    blocked_until = Column(DateTime, nullable=True)
    referral_earnings = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    verification_code = Column(String, nullable=True)

class Offer(Base):
    __tablename__ = "offers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    sell_currency = Column(String)
    sell_amount = Column(Float)
    buy_currency = Column(String)
    payment_method = Column(String)
    contact = Column(String)
    status = Column(String, default="active")
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_action = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", foreign_keys=[user_id])
    buyer = relationship("User", foreign_keys=[buyer_id])

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    text = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Dispute(Base):
    __tablename__ = "disputes"
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"))
    screenshot = Column(String)
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

class Referral(Base):
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"))
    referred_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class AdminNotification(Base):
    __tablename__ = "admin_notifications"
    id = Column(Integer, primary_key=True, index=True)
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Хэширование паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка email и SMS
email_sender = SMTP(hostname="smtp.gmail.com", port=587, use_tls=False, start_tls=True, username=os.getenv("EMAIL_USER", "test@example.com"), password=os.getenv("EMAIL_PASS", "testpass"))
twilio_client = Client(os.getenv("TWILIO_SID", "test_sid"), os.getenv("TWILIO_AUTH_TOKEN", "test_token"))

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

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = os.getenv("EMAIL_USER", "test@example.com")
    msg["To"] = to_email
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(email_sender.sendmail(os.getenv("EMAIL_USER", "test@example.com"), to_email, msg.as_string()))
    loop.close()

def send_sms(to_phone, body):
    twilio_client.messages.create(
        body=body,
        from_=os.getenv("TWILIO_PHONE", "+1234567890"),
        to=to_phone
    )

def notify_admin(message):
    db = next(get_db())
    notification = AdminNotification(message=message)
    db.add(notification)
    db.commit()
    send_email("admin@example.com", "Уведомление", message)
    send_sms("+1234567890", message)

def check_expired_offers():
    db = next(get_db())
    offers = db.query(Offer).filter(Offer.status == "in-progress").all()
    for offer in offers:
        if (datetime.utcnow() - offer.last_action).total_seconds() > 1800:  # 30 минут
            offer.status = "active"
            offer.buyer_id = None
            seller = db.query(User).filter(User.id == offer.user_id).first()
            seller.balance += offer.sell_amount
            buyer = db.query(User).filter(User.id == offer.buyer_id).first()
            if buyer:
                buyer.cancellations += 1
                if buyer.cancellations >= 10:
                    buyer.blocked_until = datetime.utcnow() + timedelta(hours=24)
                    notify_admin(f"Пользователь {buyer.id} заблокирован на 24 часа из-за 10 отмен")
            db.commit()

def daily_report():
    db = next(get_db())
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    transactions = db.query(Transaction).filter(Transactions.created_at >= today).all()
    total_earnings = sum(t.commission for t in transactions)
    active_users = db.query(User).filter(User.trades_completed > 0).count()
    notify_admin(f"Отчёт за день: Заработано {total_earnings} USDT, активных пользователей: {active_users}")

schedule.every().day.at("00:00").do(daily_report)
schedule.every(5).minutes.do(check_expired_offers)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=run_scheduler, daemon=True).start()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/register")
async def register(email: str = Form(...), phone: str = Form(...), password: str = Form(...), referral_code: str = Form(None)):
    db = next(get_db())
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    verification_code = str(hash(email + phone) % 1000000).zfill(6)
    hashed_password = pwd_context.hash(password)
    new_referral_code = str(hash(email) % 1000000).zfill(6)
    user = User(email=email, phone=phone, password=hashed_password, referral_code=new_referral_code, verified=False)
    user.verification_code = verification_code
    db.add(user)
    db.commit()
    if referral_code:
        referrer = db.query(User).filter(User.referral_code == referral_code).first()
        if referrer:
            referral = Referral(referrer_id=referrer.id, referred_id=user.id)
            db.add(referral)
            db.commit()
    send_email(email, "Код подтверждения", f"Ваш код: {verification_code}")
    send_sms(phone, f"Ваш код: {verification_code}")
    return {"message": "Код отправлен", "verification_code": verification_code}

@app.post("/verify")
async def verify(email: str = Form(...), code: str = Form(...)):
    db = next(get_db())
    user = db.query(User).filter(User.email == email).first()
    if not user or user.verification_code != code:
        raise HTTPException(status_code=400, detail="Неверный код")
    user.verified = True
    user.verification_code = None
    db.commit()
    return {"message": "Верификация успешна"}

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    db = next(get_db())
    user = db.query(User).filter(User.email == email).first()
    if not user or not pwd_context.verify(password, user.password) or not user.verified:
        raise HTTPException(status_code=400, detail="Неверные данные или не верифицирован")
    if user.blocked_until and user.blocked_until > datetime.utcnow():
        raise HTTPException(status_code=403, detail="Аккаунт заблокирован")
    expire = datetime.utcnow() + timedelta(hours=1)
    token_payload = {"user_id": user.id, "exp": expire}
    token = jwt.encode(token_payload, os.getenv("SECRET_KEY", "your-secret-key"), algorithm="HS256")
    return {"token": token, "user_id": user.id}

@app.get("/profile")
async def get_profile(user_id: int, token: str):
    payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
    if payload["user_id"] != user_id:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {
        "email": user.email,
        "balance": user.balance,
        "trades_completed": user.trades_completed,
        "cancellations": user.cancellations,
        "referral_code": user.referral_code,
        "referral_earnings": user.referral_earnings,
        "passport_verified": user.passport_verified
    }

@app.post("/upload-passport")
async def upload_passport(user_id: int, token: str, passport: UploadFile = File(...)):
    payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
    if payload["user_id"] != user_id:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    content = await passport.read()
    with open(f"passports/{user_id}.jpg", "wb") as f:
        f.write(content)
    user.passport_file = f"passports/{user_id}.jpg"
    db.commit()
    notify_admin(f"Пользователь {user_id} загрузил паспорт для верификации")
    return {"message": "Паспорт загружен"}

@app.post("/deposit")
async def deposit(user_id: int = Form(...), amount: float = Form(...), currency: str = Form(...), network: str = Form(...), token: str = Form(...)):
    payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
    if payload["user_id"] != user_id:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Сумма должна быть больше 0")
    if currency != "USDT":  # Конвертация в USDT
        amount = amount * 0.99  # Примерная конвертация
    user.balance += amount
    db.commit()
    return {"message": "Баланс пополнен", "new_balance": user.balance}

@app.post("/create-offer")
async def create_offer(user_id: int = Form(...), sell_currency: str = Form(...), sell_amount: float = Form(...), buy_currency: str = Form(...), payment_method: str = Form(...), contact: str = Form(...), token: str = Form(...)):
    payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
    if payload["user_id"] != user_id:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.balance < sell_amount:
        raise HTTPException(status_code=400, detail="Недостаточно средств")
    user.balance -= sell_amount
    offer = Offer(user_id=user_id, sell_currency=sell_currency, sell_amount=sell_amount, buy_currency=buy_currency, payment_method=payment_method, contact=contact)
    db.add(offer)
    db.commit()
    return {"message": "Объявление создано", "seller_balance": user.balance}

@app.get("/offers")
async def get_offers(sell_currency: str = None, buy_currency: str = None, payment_method: str = None, min_amount: float = None, max_amount: float = None):
    db = next(get_db())
    query = db.query(Offer).filter(Offer.status == "active")
    if sell_currency:
        query = query.filter(Offer.sell_currency == sell_currency)
    if buy_currency:
        query = query.filter(Offer.buy_currency == buy_currency)
    if payment_method:
        query = query.filter(Offer.payment_method == payment_method)
    if min_amount:
        query = query.filter(Offer.sell_amount >= min_amount)
    if max_amount:
        query = query.filter(Offer.sell_amount <= max_amount)
    offers = query.all()
    return [{"id": o.id, "sell_currency": o.sell_currency, "sell_amount": o.sell_amount, "buy_currency": o.buy_currency, "payment_method": o.payment_method, "contact": o.contact} for o in offers]

@app.get("/my-offers")
async def get_my_offers(user_id: int, token: str):
    payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
    if payload["user_id"] != user_id:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    offers = db.query(Offer).filter((Offer.user_id == user_id) | (Offer.buyer_id == user_id)).all()
    return [{"id": o.id, "sell_currency": o.sell_currency, "sell_amount": o.sell_amount, "buy_currency": o.buy_currency, "payment_method": o.payment_method, "contact": o.contact, "status": o.status} for o in offers]

@app.post("/buy-offer")
async def buy_offer(offer_id: int = Form(...), buyer_id: int = Form(...), token: str = Form(...)):
    payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
    if payload["user_id"] != buyer_id:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    offer = db.query(Offer).filter(Offer.id == offer_id, Offer.status == "active").first()
    if not offer or offer.user_id == buyer_id:
        raise HTTPException(status_code=400, detail="Заявка недоступна")
    offer.buyer_id = buyer_id
    offer.status = "in-progress"
    offer.last_action = datetime.utcnow()
    seller = db.query(User).filter(User.id == offer.user_id).first()
    buyer = db.query(User).filter(User.id == buyer_id).first()
    send_email(seller.email, "Новая сделка", f"Ваша заявка #{offer_id} куплена пользователем {buyer.email}")
    send_sms(seller.phone, f"Ваша заявка #{offer_id} куплена")
    send_email(buyer.email, "Сделка открыта", f"Вы купили заявку #{offer_id} у {seller.email}")
    send_sms(buyer.phone, f"Вы купили заявку #{offer_id}")
    if offer.sell_amount >= 10000:
        notify_admin(f"Крупная сделка #{offer_id} на сумму {offer.sell_amount} USDT")
    db.commit()
    return {"message": "Заявка куплена"}

@app.post("/confirm-offer")
async def confirm_offer(offer_id: int = Form(...), user_id: int = Form(...), token: str = Form(...)):
    payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
    if payload["user_id"] != user_id:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    offer = db.query(Offer).filter(Offer.id == offer_id, Offer.status == "in-progress").first()
    if not offer:
        raise HTTPException(status_code=400, detail="Заявка не найдена")
    if offer.user_id != user_id and offer.buyer_id != user_id:
        raise HTTPException(status_code=403, detail="Вы не участвуете в сделке")
    seller = db.query(User).filter(User.id == offer.user_id).first()
    buyer = db.query(User).filter(User.id == offer.buyer_id).first()
    commission_rate = 0.005 if seller.trades_completed >= 50 else 0.005  # 0.5% для каждого
    commission = offer.sell_amount * commission_rate * 2  # Общая комиссия
    amount_to_buyer = offer.sell_amount - (offer.sell_amount * commission_rate)
    buyer.balance += amount_to_buyer
    offer.status = "completed"
    seller.trades_completed += 1
    buyer.trades_completed += 1
    transaction = Transaction(offer_id=offer_id, commission=commission)
    db
