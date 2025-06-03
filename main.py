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
import json
from typing import List, Optional

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

# Функция для конвертации крипты в USDT (заглушка для теста)
def convert_to_usdt(currency: str, amount: float) -> float:
    rates = {"USDT": 1.0, "BTC": 70000, "ETH": 3500}  # Примерные курсы
    return amount * rates.get(currency, 1.0)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/register")
async def register(email: str = Form(...), phone: str = Form(...), password: str = Form(...), referral_code: str = Form(None)):
    db = next(get_db())
    try:
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="User already exists")
        verification_code = str(hash(email + phone) % 1000000).zfill(6)
        hashed_password = pwd_context.hash(password)
        new_referral_code = str(hash(email) % 1000000).zfill(6)
        user = User(email=email, phone=phone, password=hashed_password, referral_code=new_referral_code, verified=False)
        user.verification_code = verification_code
        if referral_code:
            referrer = db.query(User).filter(User.referral_code == referral_code).first()
            if referrer:
                user.referral_earnings = 0.0
        db.add(user)
        db.commit()

        # Отправка кода на email
        async with email_sender as server:
            message = f"Subject: Verification Code\n\nYour verification code: {verification_code}"
            await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), email, message)

        return {"message": "Code sent", "verification_code": verification_code}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/verify")
async def verify(email: str = Form(...), code: str = Form(...), passport: UploadFile = File(None)):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or user.verification_code != code:
            raise HTTPException(status_code=400, detail="Invalid code")
        user.verified = True
        if passport:
            contents = await passport.read()
            # Сохранить паспорт (например, в файл или базу), пока только отметим
            user.passport_verified = False  # Требуется ручная проверка админом
        user.verification_code = None
        db.commit()
        return {"message": "Verification successful, passport pending admin approval" if passport else "Verification successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not pwd_context.verify(password, user.password) or not user.verified:
            raise HTTPException(status_code=400, detail="Invalid credentials or not verified")
        expire = datetime.utcnow() + timedelta(hours=1)
        token_payload = {"user_id": user.id, "exp": expire, "is_admin": email == "admin@example.com"}
        token = jwt.encode(token_payload, os.getenv("SECRET_KEY", "your-secret-key"), algorithm="HS256")
        return {"token": token, "user_id": user.id, "is_admin": email == "admin@example.com", "trades_completed": user.trades_completed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/deposit")
async def deposit(user_id: int = Form(...), currency: str = Form(...), amount: float = Form(...), token: str = Form(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")
        if currency == "USDT":
            user.balance += amount
        elif currency == "BTC":
            user.btc_balance += amount
        elif currency == "ETH":
            user.eth_balance += amount
        db.commit()
        return {"message": "Balance updated", "usdt_balance": user.balance, "btc_balance": user.btc_balance, "eth_balance": user.eth_balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/create-offer")
async def create_offer(user_id: int = Form(...), offer_type: str = Form(...), currency: str = Form(...), amount: float = Form(...), fiat: str = Form(...), fiat_amount: float = Form(...), payment_method: str = Form(...), contact: str = Form(...), token: str = Form(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.verified:
            raise HTTPException(status_code=400, detail="User not found or not verified")
        if user.blocked_until and user.blocked_until > datetime.utcnow():
            raise HTTPException(status_code=403, detail="User is blocked")
        if currency == "USDT" and user.balance < amount:
            raise HTTPException(status_code=400, detail="Insufficient USDT balance")
        elif currency == "BTC" and user.btc_balance < amount:
            raise HTTPException(status_code=400, detail="Insufficient BTC balance")
        elif currency == "ETH" and user.eth_balance < amount:
            raise HTTPException(status_code=400, detail="Insufficient ETH balance")
        if currency == "USDT":
            user.balance -= amount
        elif currency == "BTC":
            user.btc_balance -= amount
        elif currency == "ETH":
            user.eth_balance -= amount
        offer = Offer(
            user_id=user_id,
            offer_type=offer_type,
            currency=currency,
            amount=amount,
            fiat=fiat,
            fiat_amount=fiat_amount,
            payment_method=payment_method,
            contact=contact
        )
        db.add(offer)
        db.commit()
        return {"message": "Offer created", "usdt_balance": user.balance, "btc_balance": user.btc_balance, "eth_balance": user.eth_balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

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
async def get_my_offers(user_id: int, token: str):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    db = next(get_db())
    try:
        offers = db.query(Offer).filter((Offer.user_id == user_id) | (Offer.buyer_id == user_id)).all()
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

@app.post("/buy-offer")
async def buy_offer(offer_id: int = Form(...), buyer_id: int = Form(...), token: str = Form(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != buyer_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    db = next(get_db())
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id, Offer.status == "active").first()
        if not offer or offer.user_id == buyer_id:
            raise HTTPException(status_code=400, detail="Offer unavailable")
        buyer = db.query(User).filter(User.id == buyer_id).first()
        if offer.currency == "USDT" and buyer.balance < offer.amount:
            raise HTTPException(status_code=400, detail="Insufficient USDT balance")
        elif offer.currency == "BTC" and buyer.btc_balance < offer.amount:
            raise HTTPException(status_code=400, detail="Insufficient BTC balance")
        elif offer.currency == "ETH" and buyer.eth_balance < offer.amount:
            raise HTTPException(status_code=400, detail="Insufficient ETH balance")
        offer.buyer_id = buyer_id
        offer.status = "pending"
        offer.frozen_amount = offer.amount
        if offer.currency == "USDT":
            buyer.balance -= offer.amount
        elif offer.currency == "BTC":
            buyer.btc_balance -= offer.amount
        elif offer.currency == "ETH":
            buyer.eth_balance -= offer.amount
        db.commit()
        # Уведомление о начале сделки
        seller = db.query(User).filter(User.id == offer.user_id).first()
        async with email_sender as server:
            message = f"Subject: New Trade Started\n\nYour offer #{offer.id} has been accepted by a buyer."
            await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), seller.email, message)
        return {"message": "Offer bought, awaiting confirmation"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/confirm-offer")
async def confirm_offer(offer_id: int = Form(...), user_id: int = Form(...), token: str = Form(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    db = next(get_db())
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer:
            raise HTTPException(status_code=400, detail="Offer not found")
        if offer.user_id != user_id and offer.buyer_id != user_id:
            raise HTTPException(status_code=403, detail="You are not part of this trade")
        if offer.user_id == user_id:
            offer.seller_confirmed = True
        elif offer.buyer_id == user_id:
            offer.buyer_confirmed = True
        if offer.seller_confirmed and offer.buyer_confirmed:
            seller = db.query(User).filter(User.id == offer.user_id).first()
            buyer = db.query(User).filter(User.id == offer.buyer_id).first()
            commission_rate = 0.005 if seller.trades_completed < 50 else 0.0025
            commission = offer.fiat_amount * commission_rate * 2  # 0.5% от каждого
            usdt_commission = convert_to_usdt(offer.currency, commission)
            amount_to_buyer = offer.amount
            amount_to_seller = offer.fiat_amount - commission
            # Начисление крипты покупателю
            if offer.currency == "USDT":
                buyer.balance += amount_to_buyer
            elif offer.currency == "BTC":
                buyer.btc_balance += amount_to_buyer
            elif offer.currency == "ETH":
                buyer.eth_balance += amount_to_buyer
            seller.balance += amount_to_seller  # Фиат продавцу
            offer.status = "completed"
            transaction = Transaction(offer_id=offer_id, commission=usdt_commission)
            db.add(transaction)
            offer.frozen_amount = 0
            buyer.trades_completed += 1
            seller.trades_completed += 1
            # Referral earnings
            if seller.referral_code:
                referrer = db.query(User).filter(User.referral_code == seller.referral_code).first()
                if referrer:
                    referrer_earnings = usdt_commission * 0.20
                    referrer.referral_earnings += referrer_earnings
            # Уведомление о завершении сделки
            async with email_sender as server:
                message = f"Subject: Trade Completed\n\nYour trade #{offer_id} has been completed."
                await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), seller.email, message)
                await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), buyer.email, message)
            # Проверка на крупную сделку
            if offer.fiat_amount * convert_to_usdt(offer.currency, 1) >= 10000:
                async with email_sender as server:
                    message = f"Subject: Large Trade\n\nTrade #{offer_id} for {offer.fiat_amount} {offer.fiat} detected."
                    await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), "admin@example.com", message)
            db.commit()
            return {"message": "Trade completed", "usdt_balance": buyer.balance, "btc_balance": buyer.btc_balance, "eth_balance": buyer.eth_balance}
        db.commit()
        return {"message": "Confirmation received, awaiting other party"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/cancel-offer")
async def cancel_offer(offer_id: int = Form(...), user_id: int = Form(...), token: str = Form(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    db = next(get_db())
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer or offer.status not in ["pending", "active"]:
            raise HTTPException(status_code=400, detail="Offer not cancellable")
        if offer.user_id != user_id and offer.buyer_id != user_id:
            raise HTTPException(status_code=403, detail="You are not part of this trade")
        user = db.query(User).filter(User.id == user_id).first()
        user.cancellations += 1
        if user.cancellations >= 10:
            user.blocked_until = datetime.utcnow() + timedelta(hours=24)
            async with email_sender as server:
                message = f"Subject: Account Blocked\n\nYour account has been blocked for 24 hours due to excessive cancellations."
                await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), user.email, message)
        if offer.frozen_amount > 0:
            if offer.user_id == user_id:
                seller = db.query(User).filter(User.id == offer.user_id).first()
                if offer.currency == "USDT":
                    seller.balance += offer.frozen_amount
                elif offer.currency == "BTC":
                    seller.btc_balance += offer.frozen_amount
                elif offer.currency == "ETH":
                    seller.eth_balance += offer.frozen_amount
            elif offer.buyer_id == user_id:
                buyer = db.query(User).filter(User.id == offer.buyer_id).first()
                if offer.currency == "USDT":
                    buyer.balance += offer.frozen_amount
                elif offer.currency == "BTC":
                    buyer.btc_balance += offer.frozen_amount
                elif offer.currency == "ETH":
                    buyer.eth_balance += offer.frozen_amount
            offer.frozen_amount = 0
        offer.status = "cancelled"
        offer.buyer_id = None
        db.commit()
        return {"message": "Offer cancelled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/send-message")
async def send_message(offer_id: int = Form(...), user_id: int = Form(...), text: str = Form(...), token: str = Form(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    db = next(get_db())
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer or (offer.user_id != user_id and offer.buyer_id != user_id):
            raise HTTPException(status_code=403, detail="You are not part of this trade")
        message = Message(offer_id=offer_id, user_id=user_id, text=text)
        db.add(message)
        db.commit()
        # Уведомление о новом сообщении
        recipient_id = offer.buyer_id if user_id == offer.user_id else offer.user_id
        recipient = db.query(User).filter(User.id == recipient_id).first()
        async with email_sender as server:
            message = f"Subject: New Message\n\nYou have a new message for offer #{offer_id}: {text}"
            await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), recipient.email, message)
        return {"message": "Message sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/get-messages")
async def get_messages(offer_id: int, user_id: int, token: str):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    db = next(get_db())
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer or (offer.user_id != user_id and offer.buyer_id != user_id):
            raise HTTPException(status_code=403, detail="You are not part of this trade")
        messages = db.query(Message).filter(Message.offer_id == offer_id).all()
        return [{
            "id": m.id,
            "user_id": m.user_id,
            "user_email": m.user.email,
            "text": m.text,
            "created_at": m.created_at
        } for m in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/create-dispute")
async def create_dispute(offer_id: int = Form(...), user_id: int = Form(...), screenshot: UploadFile = File(None), video: UploadFile = File(None), token: str = Form(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    db = next(get_db())
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer or (offer.user_id != user_id and offer.buyer_id != user_id):
            raise HTTPException(status_code=403, detail="You are not part of this trade")
        if offer.frozen_amount <= 0:
            raise HTTPException(status_code=400, detail="No funds frozen for this offer")
        screenshot_path = None
        video_path = None
        if screenshot:
            contents = await screenshot.read()
            screenshot_path = f"disputes/{offer_id}_{user_id}_screenshot.jpg"
            # Сохранить файл (например, в файловую систему)
        if video:
            contents = await video.read()
            video_path = f"disputes/{offer_id}_{user_id}_video.mp4"
            # Сохранить файл
        dispute = Dispute(offer_id=offer_id, user_id=user_id, screenshot=screenshot_path, video=video_path)
        db.add(dispute)
        offer.status = "disputed"
        db.commit()
        # Уведомление админу
        async with email_sender as server:
            message = f"Subject: New Dispute\n\nDispute created for offer #{offer_id}. Please review."
            await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), "admin@example.com", message)
        return {"message": "Dispute created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/get-disputes")
async def get_disputes(user_id: int, token: str):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if not payload.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin access required")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    db = next(get_db())
    try:
        disputes = db.query(Dispute).all()
        return [{"id": d.id, "offer_id": d.offer_id, "user_id": d.user_id, "screenshot": d.screenshot, "video": d.video, "status": d.status, "resolution": d.resolution, "created_at": d.created_at} for d in disputes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/resolve-dispute")
async def resolve_dispute(dispute_id: int = Form(...), resolution: str = Form(...), action: str = Form(...), token: str = Form(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if not payload.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin access required")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    db = next(get_db())
    try:
        dispute = db.query(Dispute).filter(Dispute.id == dispute_id, Dispute.status == "open").first()
        if not dispute:
            raise HTTPException(status_code=400, detail="Dispute not found or already resolved")
        offer = db.query(Offer).filter(Offer.id == dispute.offer_id).first()
        if not offer:
            raise HTTPException(status_code=400, detail="Offer not found")
        if action == "resolve":
            commission_rate = 0.005
            commission = offer.fiat_amount * commission_rate * 2
            usdt_commission = convert_to_usdt(offer.currency, commission)
            amount_to_buyer = offer.amount
            amount_to_seller = offer.fiat_amount - commission
            buyer = db.query(User).filter(User.id == offer.buyer_id).first()
            seller = db.query(User).filter(User.id == offer.user_id).first()
            if offer.currency == "USDT":
                buyer.balance += amount_to_buyer
            elif offer.currency == "BTC":
                buyer.btc_balance += amount_to_buyer
            elif offer.currency == "ETH":
                buyer.eth_balance += amount_to_buyer
            seller.balance += amount_to_seller
            transaction = Transaction(offer_id=offer.id, commission=usdt_commission)
            db.add(transaction)
            offer.status = "completed"
            offer.frozen_amount = 0
        elif action == "cancel":
            seller = db.query(User).filter(User.id == offer.user_id).first()
            buyer = db.query(User).filter(User.id == offer.buyer_id).first()
            if offer.currency == "USDT":
                buyer.balance += offer.frozen_amount
            elif offer.currency == "BTC":
                buyer.btc_balance += offer.frozen_amount
            elif offer.currency == "ETH":
                buyer.eth_balance += offer.frozen_amount
            offer.frozen_amount = 0
            offer.status = "cancelled"
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        dispute.status = "resolved"
        dispute.resolution = resolution
        db.commit()
        # Уведомление участников
        async with email_sender as server:
            message = f"Subject: Dispute Resolved\n\nDispute #{dispute_id} for offer #{offer.id} has been resolved. Action: {action}. Resolution: {resolution}"
            await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), buyer.email, message)
            await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), seller.email, message)
        return {"message": "Dispute resolved", "action": action}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/admin-stats")
async def admin_stats(token: str):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if not payload.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin access required")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    db = next(get_db())
    try:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        transactions = db.query(Transaction).filter(Transaction.created_at >= today).all()
        total_earnings_today = sum(t.commission for t in transactions)
        total_earnings = sum(t.commission for t in db.query(Transaction).all())
        active_users = db.query(User).filter(User.verified == True, User.blocked_until == None).count()
        large_trades = db.query(Offer).filter(Offer.fiat_amount * convert_to_usdt(Offer.currency, 1) >= 10000, Offer.status == "completed").all()
        return {
            "earnings_today": total_earnings_today,
            "earnings_total": total_earnings,
            "active_users": active_users,
            "large_trades": [{"id": t.id, "fiat_amount": t.fiat_amount, "fiat": t.fiat, "created_at": t.created_at} for t in large_trades]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/admin-users")
async def admin_users(token: str):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if not payload.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin access required")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    db = next(get_db())
    try:
        users = db.query(User).all()
        return [{
            "id": u.id,
            "email": u.email,
            "trades_completed": u.trades_completed,
            "balance": u.balance,
            "cancellations": u.cancellations,
            "blocked_until": u.blocked_until,
            "verified": u.verified
        } for u in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/reset-db")
async def reset_db():
    db = next(get_db())
    try:
        db.query(Transaction).delete()
        db.query(Dispute).delete()
        db.query(Message).delete()
        db.query(Offer).delete()
        db.query(User).delete()
        db.commit()
        return {"message": "Database reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
