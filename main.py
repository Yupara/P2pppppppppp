from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
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
templates = Jinja2Templates(directory="templates")

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
    buyer_id = Column(Integer, ForeignKey("users.id"))
    buyer_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", foreign_keys=[user_id])
    buyer = relationship("User", foreign_keys=[buyer_id])

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("users.id"))
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
email_sender = SMTP(hostname="smtp.gmail.com", 
                    port=587, 
                    use_tls=False, 
                    start_tls=True, 
                    username=os.getenv("EMAIL_USER", "test@example.com"), 
                    password=os.getenv("EMAIL_PASS", "testpass"))

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
    print(f"Received request: email={email}, phone={phone}, password={password}, referral_code={referral_code}")
    db = next(get_db())
    try:
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="Пользователь уже создан")
        verification_code = str(hash(email + phone) % 1000000).zfill(6)
        hashed_password = pwd_context.hash(password)
        new_referral_code = str(hash(email) % 1000000).zfill(6)
        user = User(email=email, phone=phone, password=hashed_password, referral_code=new_referral_code, verified=False)
        user.verification_code = verification_code
        db.add(user)
        db.commit()

        # Отправка email (временно отключено)
        # async with email_sender as server:
        #     message = f"Subject: Код верификации\n\nВаш код верификации: {verification_code}"
        #     await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), email, message)

        # Отправка SMS через Twilio (временно отключено)
        # twilio_client.messages.create_offer(
        #     body=f"Verification code: {verification_code}",
        #     from_=os.getenv("TWILIO_PHONE", "+1234567890"),
        #     to=phone
        # )
        return {"message": "Код отправлен", "verification_code": verification_code}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error in /register: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/verify")
async def verify(email: str = Form(...), code: str = Form(...)):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or user.verification_code != code:
            raise HTTPException(status_code=400, detail="Неверный код")
        user.verified = True
        user.verification_code = None
        db.commit()
        return {"message": "Верификация прошла успешно"}
    except Exception as e:
        print(f"Error in /verify: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not pwd_context.verify(password, user.password) or not user.verified:
            raise HTTPException(status_code=400, detail="Неверные данные или пользователь не верифицирован")
        # Добавляем срок действия токена (1 час)
        expire = datetime.utcnow() + timedelta(hours=1)
        token_payload = {"user_id": user.id, "exp": expire}
        token = jwt.encode(token_payload, os.getenv("SECRET_KEY", "your-secret-key"), algorithm="HS256")
        return {"token": token, "user_id": user.id}
    except Exception as e:
        print(f"Error in /login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/create-offer")
async def create_offer(user_id: int = Form(...), sell_currency: str = Form(...), sell_amount: float = Form(...), buy_currency: str = Form(...), payment_method: str = Form(...), contact: str = Form(...), token: str = Form(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != user_id:
            raise HTTPException(status_code=401, detail="Недействительный токен")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    try:
        offer = Offer(user_id=user_id, sell_currency=sell_currency, sell_amount=sell_amount, buy_currency=buy_currency, payment_method=payment_method, contact=contact)
        db.add(offer)
        db.commit()
        return {"message": "Заявка создана"}
    except Exception as e:
        print(f"Error in /create-offer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/offers")
async def get_offers(sell_currency: str = None, buy_currency: str = None, payment_method: str = None, min_amount: float = None):
    db = next(get_db())
    try:
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
    except Exception as e:
        print(f"Error in /offers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/buy-offer")
async def buy_offer(offer_id: int = Form(...), buyer_id: int = Form(...), token: str = Form(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != buyer_id:
            raise HTTPException(status_code=401, detail="Недействительный токен")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id, Offer.status == "active").first()
        if not offer or offer.user_id == buyer_id:
            raise HTTPException(status_code=400, detail="Заявка недоступна")
        offer.buyer_id = buyer_id
        offer.status = "in-progress"
        db.commit()
        return {"message": "Заявка куплена"}
    except Exception as e:
        print(f"Error in /buy-offer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/confirm-offer")
async def confirm_offer(offer_id: int = Form(...), user_id: int = Form(...), token: str = Form(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != user_id:
            raise HTTPException(status_code=401, detail="Недействительный токен")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id, Offer.status == "in-progress").first()
        if not offer:
            raise HTTPException(status_code=400, detail="Заявка не найдена или не в процессе")
        if offer.user_id != user_id and offer.buyer_id != user_id:
            raise HTTPException(status_code=403, detail="Вы не участвуете в этой сделке")
        offer.status = "completed"
        # Обновляем статистику пользователей
        seller = db.query(User).filter(User.id == offer.user_id).first()
        buyer = db.query(User).filter(User.id == offer.buyer_id).first()
        seller.trades_completed += 1
        buyer.trades_completed += 1
        # Добавляем комиссию в таблицу transactions
        commission = offer.sell_amount * 0.01  # 1% комиссии
        transaction = Transaction(offer_id=offer_id, commission=commission)
        db.add(transaction)
        db.commit()
        return {"message": "Сделка завершена"}
    except Exception as e:
        print(f"Error in /confirm-offer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/cancel-offer")
async def cancel_offer(offer_id: int = Form(...), user_id: int = Form(...), token: str = Form(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != user_id:
            raise HTTPException(status_code=401, detail="Недействительный токен")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id, Offer.status == "in-progress").first()
        if not offer:
            raise HTTPException(status_code=400, detail="Заявка не найдена или не в процессе")
        if offer.user_id != user_id and offer.buyer_id != user_id:
            raise HTTPException(status_code=403, detail="Вы не участвуете в этой сделке")
        offer.status = "active"
        offer.buyer_id = None
        # Увеличиваем счётчик отмен
        user = db.query(User).filter(User.id == user_id).first()
        user.cancellations += 1
        db.commit()
        return {"message": "Сделка отменена"}
    except Exception as e:
        print(f"Error in /cancel-offer: {str(e)}")
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
        return {"message": "База данных очищена"}
    except Exception as e:
        print(f"Error in /reset-db: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
