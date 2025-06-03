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

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/register")
async def register(email: str = Form(...), phone: str = Form(...), password: str = Form(...), referral_code: str = Form(None)):
    print(f"Received request: email={email}, phone={phone}, password={password}, referral_code={referral_code}")
    db = next(get_db())
    try:
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="Пользователь уже существует")
        verification_code = str(hash(email + phone) % 1000000).zfill(6)
        hashed_password = pwd_context.hash(password)
        new_referral_code = str(hash(email) % 1000000).zfill(6)
        user = User(email=email, phone=phone, password=hashed_password, referral_code=new_referral_code, verified=False)
        user.verification_code = verification_code
        db.add(user)
        db.commit()

        # Отправка email (временно отключено)
        # async with email_sender as server:
        #     message = f"Subject: Код подтверждения\n\nВаш код подтверждения: {verification_code}"
        #     await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), email, message)

        # Отправка SMS через Twilio (временно отключено)
        # twilio_client.messages.create(
        #     body=f"Ваш код подтверждения: {verification_code}",
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
        return {"message": "Верификация успешна"}
    except Exception as e:
        print(f"Error in /verify: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not pwd_context.verify(password, user.password) or not user.verified:
            raise HTTPException(status_code=400, detail="Неверные данные или не верифицирован")
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
        # Здесь можно добавить комиссию в таблицу transactions
        commission = offer.sell_amount * 0.01  # Например, 1% комиссии
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

@app.post("/send-message")
async def send_message(offer_id: int = Form(...), user_id: int = Form(...), text: str = Form(...), token: str = Form(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != user_id:
            raise HTTPException(status_code=401, detail="Недействительный токен")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer:
            raise HTTPException(status_code=400, detail="Заявка не найдена")
        if offer.user_id != user_id and offer.buyer_id != user_id:
            raise HTTPException(status_code=403, detail="Вы не участвуете в этой сделке")
        message = Message(offer_id=offer_id, user_id=user_id, text=text)
        db.add(message)
        db.commit()
        return {"message": "Сообщение отправлено"}
    except Exception as e:
        print(f"Error in /send-message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/get-messages")
async def get_messages(offer_id: int, user_id: int, token: str):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != user_id:
            raise HTTPException(status_code=401, detail="Недействительный токен")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer:
            raise HTTPException(status_code=400, detail="Заявка не найдена")
        if offer.user_id != user_id and offer.buyer_id != user_id:
            raise HTTPException(status_code=403, detail="Вы не участвуете в этой сделке")
        messages = db.query(Message).filter(Message.offer_id == offer_id).all()
        return [{"id": m.id, "user_id": m.user_id, "text": m.text, "created_at": m.created_at} for m in messages]
    except Exception as e:
        print(f"Error in /get-messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/create-dispute")
async def create_dispute(offer_id: int = Form(...), user_id: int = Form(...), screenshot: str = Form(None), video: str = Form(None), token: str = Form(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != user_id:
            raise HTTPException(status_code=401, detail="Недействительный токен")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer:
            raise HTTPException(status_code=400, detail="Заявка не найдена")
        if offer.user_id != user_id and offer.buyer_id != user_id:
            raise HTTPException(status_code=403, detail="Вы не участвуете в этой сделке")
        dispute = Dispute(offer_id=offer_id, screenshot=screenshot, video=video)
        db.add(dispute)
        db.commit()

        # Отправка email уведомления продавцу и покупателю
        seller = db.query(User).filter(User.id == offer.user_id).first()
        buyer = db.query(User).filter(User.id == offer.buyer_id).first()
        if seller and buyer:
            async with email_sender as server:
                seller_message = f"Subject: Новый спор\n\nСпор создан для вашей заявки #{offer_id}. Пожалуйста, проверьте детали."
                buyer_message = f"Subject: Новый спор\n\nВы создали спор для заявки #{offer_id}. Ожидайте решения."
                await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), seller.email, seller_message)
                await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), buyer.email, buyer_message)

            # Отправка SMS уведомления (временно только продавцу)
            twilio_client.messages.create(
                body=f"Новый спор для заявки #{offer_id}. Проверьте email.",
                from_=os.getenv("TWILIO_PHONE", "+1234567890"),
                to=seller.phone
            )

        return {"message": "Спор создан"}
    except Exception as e:
        print(f"Error in /create-dispute: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/get-disputes")
async def get_disputes(user_id: int, token: str):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != user_id:
            raise HTTPException(status_code=401, detail="Недействительный токен")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    try:
        # Находим все сделки, в которых участвует пользователь
        offers = db.query(Offer).filter((Offer.user_id == user_id) | (Offer.buyer_id == user_id)).all()
        offer_ids = [offer.id for offer in offers]
        # Находим все споры для этих сделок
        disputes = db.query(Dispute).filter(Dispute.offer_id.in_(offer_ids)).all()
        return [{"id": d.id, "offer_id": d.offer_id, "screenshot": d.screenshot, "video": d.video, "status": d.status, "resolution": d.resolution, "created_at": d.created_at} for d in disputes]
    except Exception as e:
        print(f"Error in /get-disputes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/resolve-dispute")
async def resolve_dispute(dispute_id: int = Form(...), admin_id: int = Form(...), resolution: str = Form(...), action: str = Form(...), token: str = Form(...)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        if payload["user_id"] != admin_id:
            raise HTTPException(status_code=401, detail="Недействительный токен")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    db = next(get_db())
    try:
        # Проверяем, что спор существует и ещё открыт
        dispute = db.query(Dispute).filter(Dispute.id == dispute_id, Dispute.status == "open").first()
        if not dispute:
            raise HTTPException(status_code=400, detail="Спор не найден или уже разрешён")
        
        # Находим связанную сделку
        offer = db.query(Offer).filter(Offer.id == dispute.offer_id).first()
        if not offer:
            raise HTTPException(status_code=400, detail="Заявка не найдена")

        # Обновляем статус спора и добавляем решение
        dispute.status = "resolved" if action == "resolve" else "cancelled"
        dispute.resolution = resolution
        db.commit()

        # Обновляем статус сделки в зависимости от решения
        if action == "resolve":
            offer.status = "completed"
        elif action == "cancel":
            offer.status = "active"
            offer.buyer_id = None  # Сбрасываем покупателя
            # Увеличиваем счётчик отмен у покупателя
            buyer = db.query(User).filter(User.id == offer.buyer_id).first()
            if buyer:
                buyer.cancellations += 1
        else:
            raise HTTPException(status_code=400, detail="Недопустимое действие. Используйте 'resolve' или 'cancel'")
        db.commit()

        # Отправка email уведомления продавцу, покупателю и администратору
        seller = db.query(User).filter(User.id == offer.user_id).first()
        buyer = db.query(User).filter(User.id == offer.buyer_id).first()
        admin = db.query(User).filter(User.id == admin_id).first()
        if seller and buyer and admin:
            async with email_sender as server:
                seller_message = f"Subject: Спор разрешён\n\nСпор для заявки #{offer.id} разрешён. Решение: {resolution}"
                buyer_message = f"Subject: Спор разрешён\n\nСпор для заявки #{offer.id} разрешён. Решение: {resolution}"
                admin_message = f"Subject: Спор разрешён\n\nВы решили спор для заявки #{offer.id}. Решение: {resolution}"
                await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), seller.email, seller_message)
                await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), buyer.email, buyer_message)
                await server.sendmail(os.getenv("EMAIL_USER", "test@example.com"), admin.email, admin_message)

            # Отправка SMS уведомления (временно только продавцу)
            twilio_client.messages.create(
                body=f"Спор для заявки #{offer.id} разрешён. Решение: {resolution}",
                from_=os.getenv("TWILIO_PHONE", "+1234567890"),
                to=seller.phone
            )

        return {"message": "Спор разрешён", "resolution": resolution}
    except Exception as e:
        print(f"Error in /resolve-dispute: {str(e)}")
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
