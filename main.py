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

        # Отправка кода на email (временно тестовый код)
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
        return {"token": token, "user_id": user.id, "is_admin": email == "admin@example.com"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/create-offer")
async def create_offer(user_id: int = Form(...), offer_type: str = Form(...), currency: str = Form(...), amount: float = Form(...), fiat: str = Form(...), payment_method: str = Form(...), contact: str = Form(...), token: str = Form(...)):
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
        if user.balance < amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        user.balance -= amount
        offer = Offer(user_id=user_id, sell_currency=currency if offer_type == "sell" else fiat, sell_amount=amount if offer_type == "sell" else 0, buy_currency=fiat if offer_type == "sell" else currency, payment_method=payment_method, contact=contact)
        db.add(offer)
        db.commit()
        return {"message": "Offer created", "user_balance": user.balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/offers")
async def get_offers(offer_type: str = None, currency: str = None, fiat: str = None, payment_method: str = None, min_amount: float = None):
    db = next(get_db())
    try:
        query = db.query(Offer).filter(Offer.status == "active")
        if offer_type:
            query = query.filter(Offer.sell_currency == (fiat if offer_type == "sell" else currency) if offer_type == "sell" else Offer.buy_currency == currency)
        if currency:
            query = query.filter(Offer.sell_currency == currency or Offer.buy_currency == currency)
        if fiat:
            query = query.filter(Offer.sell_currency == fiat or Offer.buy_currency == fiat)
        if payment_method and payment_method != "all":
            query = query.filter(Offer.payment_method == payment_method)
        if min_amount:
            query = query.filter(Offer.sell_amount >= min_amount)
        offers = query.all()
        return [{"id": o.id, "user_id": o.user_id, "sell_currency": o.sell_currency, "sell_amount": o.sell_amount, "buy_currency": o.buy_currency, "payment_method": o.payment_method, "contact": o.contact, "status": o.status} for o in offers]
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
        offer.buyer_id = buyer_id
        offer.status = "pending"
        offer.frozen_amount = offer.sell_amount
        db.commit()
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
            commission_rate = 0.005 if offer.user.trades_completed < 50 else 0.0025
            commission = offer.sell_amount * commission_rate
            amount_to_buyer = offer.sell_amount - commission
            buyer = db.query(User).filter(User.id == offer.buyer_id).first()
            seller = db.query(User).filter(User.id == offer.user_id).first()
            buyer.balance += amount_to_buyer
            seller.balance += 0  # Seller gets nothing until admin review (for disputes)
            offer.status = "completed"
            transaction = Transaction(offer_id=offer_id, commission=commission)
            db.add(transaction)
            offer.frozen_amount = 0
            buyer.trades_completed += 1
            seller.trades_completed += 1
            # Referral earnings
            if seller.referral_code:
                referrer = db.query(User).filter(User.referral_code == seller.referral_code).first()
                if referrer:
                    referrer_earnings = commission * 0.20
                    referrer.referral_earnings += referrer_earnings
            db.commit()
            return {"message": "Trade completed", "buyer_balance": buyer.balance}
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
        if offer.frozen_amount > 0:
            seller = db.query(User).filter(User.id == offer.user_id).first()
            seller.balance += offer.frozen_amount
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
        return [{"id": m.id, "user_id": m.user_id, "text": m.text, "created_at": m.created_at} for m in messages]
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
        offer.frozen_amount = offer.sell_amount
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
            commission = offer.sell_amount * commission_rate
            amount_to_buyer = offer.sell_amount - commission
            buyer = db.query(User).filter(User.id == offer.buyer_id).first()
            seller = db.query(User).filter(User.id == offer.user_id).first()
            buyer.balance += amount_to_buyer
            transaction = Transaction(offer_id=offer.id, commission=commission)
            db.add(transaction)
            offer.status = "completed"
            offer.frozen_amount = 0
        elif action == "cancel":
            seller = db.query(User).filter(User.id == offer.user_id).first()
            seller.balance += offer.frozen_amount
            offer.frozen_amount = 0
            offer.status = "cancelled"
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        dispute.status = "resolved"
        dispute.resolution = resolution
        db.commit()
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
        return {"earnings_today": total_earnings_today, "earnings_total": total_earnings, "active_users": active_users}
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
