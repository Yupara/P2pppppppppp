from fastapi import FastAPI, Request, Form, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from aiosmtplib import SMTP
from datetime import datetime, timedelta
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
    theme = Column(String, default="light")  # Настройка темы

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

# Настройка email
email_sender = SMTP(
    hostname="smtp.gmail.com",
    port=587,
    use_tls=False,
    start_tls=True,
    username=os.getenv("EMAIL_USER"),
    password=os.getenv("EMAIL_PASS")
)

# Отключение Twilio
twilio_client = None
print("Twilio is disabled. SMS notifications will not be sent.")

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

# Добавление тестовых данных
def add_test_data():
    db = SessionLocal()
    try:
        # Тестовый пользователь
        test_user = db.query(User).filter(User.id == 1).first()
        if not test_user:
            new_user = User(
                id=1,
                email="test@example.com",
                phone="1234567890",
                password="test",
                referral_code="TEST123",
                balance=1000.0,
                btc_balance=0.5,
                eth_balance=2.0,
                verified=True,
                theme="dark"
            )
            db.add(new_user)

        # Тестовые офферы
        test_offer1 = db.query(Offer).filter(Offer.id == 1).first()
        if not test_offer1:
            offer1 = Offer(
                id=1,
                user_id=1,
                offer_type="sell",
                currency="USDT",
                amount=100.0,
                fiat="USD",
                fiat_amount=100.0,
                payment_method="Bank Transfer",
                contact="testuser@example.com"
            )
            db.add(offer1)
        
        test_offer2 = db.query(Offer).filter(Offer.id == 2).first()
        if not test_offer2:
            offer2 = Offer(
                id=2,
                user_id=1,
                offer_type="buy",
                currency="BTC",
                amount=0.01,
                fiat="RUB",
                fiat_amount=7000.0,
                payment_method="Crypto Wallet",
                contact="testuser@example.com"
            )
            db.add(offer2)

        # Тестовая транзакция
        test_transaction = db.query(Transaction).filter(Transaction.id == 1).first()
        if not test_transaction:
            transaction = Transaction(
                id=1,
                offer_id=1,
                commission=0.5
            )
            db.add(transaction)

        db.commit()
        print("Test data added: user_id=1, offers=2, transaction=1")
    finally:
        db.close()

# Вызываем функцию для добавления тестовых данных
add_test_data()

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

# Главная страница
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, offer_type: str = None, currency: str = None, fiat: str = None, payment_method: str = None, amount: float = None):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == 1).first()  # Тестовый пользователь
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
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        transactions = db.query(Transaction).filter(Transaction.created_at >= today).all()
        total_earnings_today = sum(t.commission for t in transactions)
        total_earnings = sum(t.commission for t in db.query(Transaction).all())
        withdrawals = sum(w.amount for w in db.query(AdminWithdrawal).all())
        available_earnings = total_earnings - withdrawals
        active_users = db.query(User).filter(User.verified == True, User.blocked_until == None).all()

        return templates.TemplateResponse("index.html", {
            "request": request,
            "offers": [{
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
            } for o in offers],
            "earnings_today": total_earnings_today,
            "total_earnings": total_earnings,
            "available_earnings": available_earnings,
            "active_users_count": len(active_users),
            "user": user,
            "is_admin": user.email == "admin@example.com"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/deposit")
async def deposit(currency: str = Form(...), amount: float = Form(...)):
    db = next(get_db())
    try:
        user_id = 1  # Тестовый пользователь
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
async def create_offer(offer_type: str = Form(...), currency: str = Form(...), amount: float = Form(...), fiat: str = Form(...), fiat_amount: float = Form(...), payment_method: str = Form(...), contact: str = Form(...)):
    db = next(get_db())
    try:
        user_id = 1  # Тестовый пользователь
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
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
async def get_my_offers():
    db = next(get_db())
    try:
        user_id = 1  # Тестовый пользователь
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
async def buy_offer(offer_id: int = Form(...)):
    db = next(get_db())
    try:
        user_id = 1  # Тестовый пользователь
        offer = db.query(Offer).filter(Offer.id == offer_id, Offer.status == "active").first()
        if not offer or offer.user_id == user_id:
            raise HTTPException(status_code=400, detail="Offer unavailable")
        buyer = db.query(User).filter(User.id == user_id).first()
        if offer.currency == "USDT" and buyer.balance < offer.amount:
            raise HTTPException(status_code=400, detail="Insufficient USDT balance")
        elif offer.currency == "BTC" and buyer.btc_balance < offer.amount:
            raise HTTPException(status_code=400, detail="Insufficient BTC balance")
        elif offer.currency == "ETH" and buyer.eth_balance < offer.amount:
            raise HTTPException(status_code=400, detail="Insufficient ETH balance")
        offer.buyer_id = user_id
        offer.status = "pending"
        offer.frozen_amount = offer.amount
        if offer.currency == "USDT":
            buyer.balance -= offer.amount
        elif offer.currency == "BTC":
            buyer.btc_balance -= offer.amount
        elif offer.currency == "ETH":
            buyer.eth_balance -= offer.amount
        db.commit()
        seller = db.query(User).filter(User.id == offer.user_id).first()
        async with email_sender as server:
            message = f"Subject: New Trade Started\n\nYour offer #{offer.id} has been accepted by a buyer."
            await server.sendmail(os.getenv("EMAIL_USER"), seller.email, message)
        return {"message": "Offer bought, awaiting confirmation"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/confirm-offer")
async def confirm_offer(offer_id: int = Form(...)):
    db = next(get_db())
    try:
        user_id = 1  # Тестовый пользователь
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
            commission = offer.fiat_amount * commission_rate * 2
            usdt_commission = convert_to_usdt(offer.currency, commission)
            amount_to_buyer = offer.amount
            amount_to_seller = offer.fiat_amount - commission
            if offer.currency == "USDT":
                buyer.balance += amount_to_buyer
            elif offer.currency == "BTC":
                buyer.btc_balance += amount_to_buyer
            elif offer.currency == "ETH":
                buyer.eth_balance += amount_to_buyer
            seller.balance += amount_to_seller
            offer.status = "completed"
            transaction = Transaction(offer_id=offer_id, commission=usdt_commission)
            db.add(transaction)
            offer.frozen_amount = 0
            buyer.trades_completed += 1
            seller.trades_completed += 1
            if seller.referral_code:
                referrer = db.query(User).filter(User.referral_code == seller.referral_code).first()
                if referrer:
                    referrer_earnings = usdt_commission * 0.20
                    referrer.referral_earnings += referrer_earnings
            async with email_sender as server:
                message = f"Subject: Trade Completed\n\nYour trade #{offer_id} has been completed."
                await server.sendmail(os.getenv("EMAIL_USER"), seller.email, message)
                await server.sendmail(os.getenv("EMAIL_USER"), buyer.email, message)
            if offer.fiat_amount * convert_to_usdt(offer.currency, 1) >= 10000:
                async with email_sender as server:
                    message = f"Subject: Large Trade\n\nTrade #{offer_id} for {offer.fiat_amount} {offer.fiat} detected."
                    await server.sendmail(os.getenv("EMAIL_USER"), "admin@example.com", message)
            db.commit()
            return {"message": "Trade completed", "usdt_balance": buyer.balance, "btc_balance": buyer.btc_balance, "eth_balance": buyer.eth_balance}
        db.commit()
        return {"message": "Confirmation received, awaiting other party"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/cancel-offer")
async def cancel_offer(offer_id: int = Form(...)):
    db = next(get_db())
    try:
        user_id = 1  # Тестовый пользователь
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer or offer.status not in ["pending", "active"]:
            raise HTTPException(status_code=400, detail="Offer not found or not cancellable")
        if offer.user_id != user_id and offer.buyer_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        user = db.query(User).filter(User.id == user_id).first()
        user.cancellations += 1
        if user.cancellations >= 10:
            user.blocked_until = datetime.utcnow() + timedelta(hours=24)
            async with email_sender as server:
                message = f"Subject: Account Blocked\n\nYour account has been blocked for 24 hours due to excessive cancellations."
                await server.sendmail(os.getenv("EMAIL_USER"), user.email, message)
        if offer.frozen_amount > 0:
            if offer.user_id == user_id:
                seller = user
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
async def send_message(offer_id: int = Form(...), text: str = Form(...)):
    db = next(get_db())
    try:
        user_id = 1  # Тестовый пользователь
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer or (offer.user_id != user_id and offer.buyer_id != user_id):
            raise HTTPException(status_code=403, detail="You are not part of this trade")
        message = Message(offer_id=offer_id, user_id=user_id, text=text)
        db.add(message)
        db.commit()
        recipient_id = offer.buyer_id if user_id == offer.user_id else offer.user_id
        recipient = db.query(User).filter(User.id == recipient_id).first()
        async with email_sender as server:
            message = f"Subject: New Message\n\nYou have a new message for offer #{offer.id}: {text}"
            await server.sendmail(os.getenv("EMAIL_USER"), recipient.email, message)
        return {"message": "Message sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/get-messages")
async def get_messages(offer_id: int):
    db = next(get_db())
    try:
        user_id = 1  # Тестовый пользователь
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer or (offer.user_id != user_id and offer.buyer_id != user_id):
            raise HTTPException(status_code=403, detail="Not authorized")
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
async def create_dispute(offer_id: int = Form(...), screenshot: UploadFile = File(None), video: UploadFile = File(None)):
    db = next(get_db())
    try:
        user_id = 1  # Тестовый пользователь
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer or (offer.user_id != user_id and offer.buyer_id != user_id):
            raise HTTPException(status_code=403, detail="Not authorized")
        if offer.frozen_amount <= 0:
            raise HTTPException(status_code=400, detail="No funds frozen for this offer")
        screenshot_path = None
        video_path = None
        if screenshot:
            contents = await screenshot.read()
            screenshot_path = f"disputes/{offer_id}_{user_id}_screenshot.jpg"
        if video:
            contents = await video.read()
            video_path = f"disputes/{offer_id}_{user_id}_video.mp4"
        dispute = Dispute(offer_id=offer_id, user_id=user_id, screenshot=screenshot_path, video=video_path)
        db.add(dispute)
        offer.status = "disputed"
        db.commit()
        async with email_sender as server:
            message = f"Subject: New Dispute\n\nDispute created for offer #{offer_id}. Please review."
            await server.sendmail(os.getenv("EMAIL_USER"), "admin@example.com", message)
        return {"message": "Dispute created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/get-disputes")
async def get_disputes():
    db = next(get_db())
    try:
        user_id = 1  # Тестовый пользователь
        user = db.query(User).filter(User.id == user_id).first()
        if not user.email == "admin@example.com":
            raise HTTPException(status_code=403, detail="Admin access required")
        disputes = db.query(Dispute).all()
        return [{"id": d.id, "offer_id": d.offer_id, "user_id": d.user_id, "screenshot": d.screenshot, "video": d.video, "status": d.status, "resolution": d.resolution, "created_at": d.created_at} for d in disputes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/resolve-dispute")
async def resolve_dispute(dispute_id: int = Form(...), resolution: str = Form(...), action: str = Form(...)):
    db = next(get_db())
    try:
        user_id = 1  # Тестовый пользователь
        user = db.query(User).filter(User.id == user_id).first()
        if not user.email == "admin@example.com":
            raise HTTPException(status_code=403, detail="Admin access required")
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
        async with email_sender as server:
            message = f"Subject: Dispute Resolved\n\nDispute #{dispute_id} for offer #{offer.id} has been resolved. Action: {action}. Resolution: {resolution}"
            await server.sendmail(os.getenv("EMAIL_USER"), buyer.email, message)
            await server.sendmail(os.getenv("EMAIL_USER"), seller.email, message)
        return {"message": "Dispute resolved", "action": action}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/admin-stats")
async def admin_stats():
    db = next(get_db())
    try:
        user_id = 1  # Тестовый пользователь
        user = db.query(User).filter(User.id == user_id).first()
        if not user.email == "admin@example.com":
            raise HTTPException(status_code=403, detail="Admin access required")
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

@app.post("/withdraw-earnings")
async def withdraw_earnings():
    db = next(get_db())
    try:
        user_id = 1  # Тестовый пользователь
        user = db.query(User).filter(User.id == user_id).first()
        if not user.email == "admin@example.com":
            raise HTTPException(status_code=403, detail="Admin access required")
        total_earnings = sum(t.commission for t in db.query(Transaction).all())
        withdrawals = sum(w.amount for w in db.query(AdminWithdrawal).all())
        available_earnings = total_earnings - withdrawals
        if available_earnings <= 0:
            raise HTTPException(status_code=400, detail="No earnings available to withdraw")
        withdrawal = AdminWithdrawal(amount=available_earnings)
        db.add(withdrawal)
        db.commit()
        async with email_sender as server:
            message = f"Subject: Earnings Withdrawn\n\n{available_earnings} USDT has been withdrawn."
            await server.sendmail(os.getenv("EMAIL_USER"), "admin@example.com", message)
        return {"message": f"Withdrawn {available_earnings} USDT"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/reset-db")
async def reset_db():
    db = next(get_db())
    try:
        db.query(AdminWithdrawal).delete()
        db.query(Transaction).delete()
        db.query(Dispute).delete()
        db.query(Message).delete()
        db.query(Offer).delete()
        db.query(User).delete()
        test_user = User(
            id=1,
            email="test@example.com",
            phone="1234567890",
            password="test",
            referral_code="TEST123",
            balance=1000.0,
            btc_balance=0.5,
            eth_balance=2.0,
            verified=True,
            theme="dark"
        )
        db.add(test_user)
        db.commit()
        return {"message": "Database reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/update-theme")
async def update_theme(theme: str = Form(...)):
    db = next(get_db())
    try:
        user_id = 1  # Тестовый пользователь
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        user.theme = theme
        db.commit()
        return {"message": "Theme updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
