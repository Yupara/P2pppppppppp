from fastapi import FastAPI, Request, Form, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi_csrf_protect import CsrfProtect
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi_websocket_pubsub import PubSubClient
import os
import logging
from typing import Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройки
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
CSRF_SECRET_KEY = os.getenv("CSRF_SECRET_KEY", "your-csrf-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///p2p_exchange.db")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Модели
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True)
    hashed_password = Column(String)
    balance = Column(Float, default=0.0)
    escrow_balance = Column(Float, default=0.0)  # Для эскроу
    verified_email = Column(Boolean, default=False)
    verified_phone = Column(Boolean, default=False)
    verified_identity = Column(Boolean, default=False)
    is_merchant = Column(Boolean, default=False)
    vip_level = Column(Integer, default=0)
    vip_progress = Column(Float, default=0.0)
    total_invested = Column(Float, default=0.0)
    notifications_enabled = Column(Boolean, default=True)
    referral_code = Column(String, unique=True)
    referred_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    orders_completed = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    avg_transfer_time = Column(Float, default=0.0)  # В минутах

class Offer(Base):
    __tablename__ = "offers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    offer_type = Column(String)  # buy/sell
    currency = Column(String)  # USDT, BTC, ETH, TON
    amount = Column(Float)
    fiat = Column(String)  # RUB, USD, EUR
    fiat_amount = Column(Float)
    payment_method = Column(String)
    contact = Column(String)
    status = Column(String, default="active")  # active, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    payment_window = Column(Integer, default=15)  # Время оплаты в минутах
    only_verified = Column(Boolean, default=False)
    only_vip = Column(Boolean, default=False)
    description = Column(Text, nullable=True)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"))
    buyer_id = Column(Integer, ForeignKey("users.id"))
    seller_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    fiat_amount = Column(Float)
    status = Column(String, default="pending")  # pending, completed, disputed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class Dispute(Base):
    __tablename__ = "disputes"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    initiator_id = Column(Integer, ForeignKey("users.id"))
    reason = Column(Text)
    status = Column(String, default="open")  # open, resolved
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Referral(Base):
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"))
    referred_id = Column(Integer, ForeignKey("users.id"))
    bonus_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# CSRF
class CsrfSettings:
    secret_key = CSRF_SECRET_KEY
    cookie_samesite = "lax"

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

# Зависимости
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Form(...), db: SessionLocal = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Роуты
@app.post("/auth/register")
async def register(email: str = Form(...), password: str = Form(...), phone: str = Form(...), referral_code: Optional[str] = Form(None), db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = pwd_context.hash(password)
    import uuid
    new_user = User(email=email, phone=phone, hashed_password=hashed_password, referral_code=str(uuid.uuid4()))
    if referral_code:
        referrer = db.query(User).filter(User.referral_code == referral_code).first()
        if referrer:
            new_user.referred_by = referrer.id
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    token = create_access_token({"sub": email})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/auth/login")
async def login(email: str = Form(...), password: str = Form(...), db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": email})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/csrf-token")
async def get_csrf_token(csrf_protect: CsrfProtect = Depends()):
    return {"csrf_token": csrf_protect.generate_csrf()}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, current_user: User = Depends(get_current_user), db: SessionLocal = Depends(get_db)):
    offers = db.query(Offer).filter(Offer.status == "active").all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": current_user,
        "offers": offers,
        "tab": "buy"
    })

@app.get("/offers/filter")
async def filter_offers(
    offer_type: str = Query("buy"),
    currency: Optional[str] = Query(None),
    fiat: Optional[str] = Query(None),
    amount: Optional[float] = Query(None),
    payment_method: Optional[str] = Query(None),
    only_verified: bool = Query(False),
    only_online: bool = Query(False),
    only_merchants: bool = Query(False),
    db: SessionLocal = Depends(get_db)
):
    query = db.query(Offer).filter(Offer.status == "active", Offer.offer_type == offer_type)
    if currency:
        query = query.filter(Offer.currency == currency)
    if fiat:
        query = query.filter(Offer.fiat == fiat)
    if amount:
        query = query.filter(Offer.amount >= amount)
    if payment_method:
        query = query.filter(Offer.payment_method == payment_method)
    if only_verified:
        query = query.join(User).filter(User.verified_identity == True)
    if only_online:
        query = query.join(User).filter(User.last_seen > datetime.utcnow() - timedelta(minutes=15))
    if only_merchants:
        query = query.join(User).filter(User.is_merchant == True)
    offers = query.all()
    return offers

@app.post("/create-offer")
async def create_offer(
    offer_type: str = Form(...),
    currency: str = Form(...),
    amount: float = Form(...),
    fiat: str = Form(...),
    fiat_amount: float = Form(...),
    payment_method: str = Form(...),
    contact: str = Form(...),
    payment_window: int = Form(15),
    only_verified: bool = Form(False),
    only_vip: bool = Form(False),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: SessionLocal = Depends(get_db),
    csrf_protect: CsrfProtect = Depends()
):
    await csrf_protect.validate_csrf(request)
    if offer_type == "sell" and current_user.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    if amount < 500 or amount > 5000:
        raise HTTPException(status_code=400, detail="Amount out of range (500-5000)")
    if only_vip and current_user.vip_level == 0:
        raise HTTPException(status_code=400, detail="VIP status required")
    offer = Offer(
        user_id=current_user.id,
        offer_type=offer_type,
        currency=currency,
        amount=amount,
        fiat=fiat,
        fiat_amount=fiat_amount,
        payment_method=payment_method,
        contact=contact,
        payment_window=payment_window,
        only_verified=only_verified,
        only_vip=only_vip,
        description=description
    )
    if offer_type == "sell":
        current_user.balance -= amount
        current_user.escrow_balance += amount  # Блокировка в эскроу
    db.add(offer)
    db.commit()
    return {"message": "Offer created", "balance": current_user.balance}

@app.post("/buy-offer/{offer_id}")
async def buy_offer(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: SessionLocal = Depends(get_db),
    csrf_protect: CsrfProtect = Depends()
):
    await csrf_protect.validate_csrf(request)
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer or offer.status != "active":
        raise HTTPException(status_code=400, detail="Offer not available")
    if offer.only_verified and not current_user.verified_identity:
        raise HTTPException(status_code=400, detail="Verification required")
    if offer.only_vip and current_user.vip_level == 0:
        raise HTTPException(status_code=400, detail="VIP status required")
    if current_user.balance < offer.fiat_amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    transaction = Transaction(
        offer_id=offer_id,
        buyer_id=current_user.id,
        seller_id=offer.user_id,
        amount=offer.amount,
        fiat_amount=offer.fiat_amount
    )
    current_user.balance -= offer.fiat_amount
    offer.status = "pending"
    db.add(transaction)
    db.commit()
    return {"message": "Transaction started", "transaction_id": transaction.id}

@app.post("/complete-transaction/{transaction_id}")
async def complete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: SessionLocal = Depends(get_db),
    csrf_protect: CsrfProtect = Depends()
):
    await csrf_protect.validate_csrf(request)
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction or transaction.status != "pending":
        raise HTTPException(status_code=400, detail="Invalid transaction")
    if transaction.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    transaction.status = "completed"
    transaction.completed_at = datetime.utcnow()
    seller = db.query(User).filter(User.id == transaction.seller_id).first()
    buyer = db.query(User).filter(User.id == transaction.buyer_id).first()
    seller.escrow_balance -= transaction.amount
    seller.balance += transaction.fiat_amount
    buyer.balance += transaction.amount
    seller.orders_completed += 1
    buyer.orders_completed += 1
    offer = db.query(Offer).filter(Offer.id == transaction.offer_id).first()
    offer.status = "completed"
    db.commit()
    return {"message": "Transaction completed"}

@app.post("/dispute/{transaction_id}")
async def create_dispute(
    transaction_id: int,
    reason: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: SessionLocal = Depends(get_db),
    csrf_protect: CsrfProtect = Depends()
):
    await csrf_protect.validate_csrf(request)
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction or transaction.status != "pending":
        raise HTTPException(status_code=400, detail="Invalid transaction")
    if transaction.buyer_id != current_user.id and transaction.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    dispute = Dispute(transaction_id=transaction_id, initiator_id=current_user.id, reason=reason)
    transaction.status = "disputed"
    db.add(dispute)
    db.commit()
    return {"message": "Dispute created", "dispute_id": dispute.id}

# WebSocket для чата
@app.websocket("/ws/chat/{transaction_id}")
async def websocket_chat(websocket: WebSocket, transaction_id: int, db: SessionLocal = Depends(get_db)):
    await websocket.accept()
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        await websocket.close(code=1008)
        return
    client = PubSubClient()
    async def on_message(data):
        await websocket.send_json(data)
    client.subscribe(f"chat_{transaction_id}", on_message)
    try:
        while True:
            data = await websocket.receive_json()
            message = ChatMessage(
                transaction_id=transaction_id,
                sender_id=data["user_id"],
                message=data["message"]
            )
            db.add(message)
            db.commit()
            await client.publish(f"chat_{transaction_id}", {
                "sender_id": message.sender_id,
                "message": message.message,
                "created_at": message.created_at.isoformat()
            })
    except WebSocketDisconnect:
        client.disconnect()

# Админка
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, current_user: User = Depends(get_current_user), db: SessionLocal = Depends(get_db)):
    if not current_user.is_admin:  # Предполагается поле is_admin в модели User
        raise HTTPException(status_code=403, detail="Admin access required")
    users = db.query(User).all()
    disputes = db.query(Dispute).filter(Dispute.status == "open").all()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "users": users,
        "disputes": disputes
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
