from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from passlib.context import CryptContext
from twilio.rest import Client
from aiosmtplib import SMTP
from datetime import datetime, timedelta
import jwt
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
# Временно убрали Jinja2Templates, так как шаблон index.html отсутствует
# templates = Jinja2Templates(directory="templates")

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
    blocked_until = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    buyer_id = Column(Integer, ForeignKey("users.id"))
    buyer_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
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
    video = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"))
    commission = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

# Хэширование паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка email с aiosmtplib
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

@app.get("/")
async def read_root():
    return JSONResponse(content={"message": "Welcome to P2P Exchange!"})

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

    # Отправка email
    message = f"Subject: Код подтверждения\n\nВаш код подтверждения: {verification_code}"
    async with email_sender as server:
        await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), email, message)

    twilio_client.messages.create(
        body=f"Ваш код подтверждения: {verification_code}",
        from_=os.getenv("TWILIO_PHONE", "+1234567890"),
        to=phone
    )
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
    token = jwt.encode({"user_id": user.id}, os.getenv("SECRET_KEY", "your-secret-key"), algorithm="HS256")
    return {"token": token, "user_id": user.id}

@app.post("/create-offer")
async def create_offer(user_id: int, sell_currency: str = Form(...), sell_amount: float = Form(...), buy_currency: str = Form(...), payment_method: str = Form(...), contact: str = Form(...), token: str = Form(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != user_id:
            raise HTTPException(status_code=401, detail="Недействительный токен")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    offer = Offer(user_id=user_id, sell_currency=sell_currency, sell_amount=sell_amount, buy_currency=buy_currency, payment_method=payment_method, contact=contact)
    db.add(offer)
    db.commit()
    return {"message": "Заявка создана"}

@app.get("/offers")
async def get_offers(sell_currency: str = None, buy_currency: str = None, payment_method: str = None, min_amount: float = None):
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
    offers = query.all()
    return [{"id": o.id, "sell_currency": o.sell_currency, "sell_amount": o.sell_amount, "buy_currency": o.buy_currency, "payment_method": o.payment_method, "contact": o.contact} for o in offers]

@app.post("/buy-offer")
async def buy_offer(offer_id: int, buyer_id: int, token: str = Form(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != buyer_id:
            raise HTTPException(status_code=401, detail="Недействительный токен")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    offer = db.query(Offer).filter(Offer.id == offer_id, Offer.status == "active").first()
    if not offer or offer.user_id == buyer_id:
        raise HTTPException(status_code=400, detail="Заявка недоступна")
    offer.buyer_id = buyer_id
    offer.status = "in-progress"
    db.commit()
    return {"message": "Заявка куплена"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
