import os
from datetime import datetime, timedelta
from uuid import uuid4
from dotenv import load_dotenv

from fastapi import (
    FastAPI, Request, Form, Depends, HTTPException
)
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from sqlalchemy import (
    create_engine, Column, Integer, String,
    Float, ForeignKey, DateTime, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# Загрузка .env
load_dotenv()

# ——— Константы ———
ADMIN_UUID = "293dd908-eac9-4082-b5e6-112d649a60bc"
DATABASE_URL = "sqlite:///./p2p.db"

# Предопределённые варианты
CRYPTOS = ["USDT", "BTC", "ETH", "TRUMP"]
FIATS = [
    ("USD", "Доллар США"), ("EUR", "Евро"), ("GBP", "Британский фунт"),
    ("RUB", "Российский рубль"), ("UAH", "Украинская гривна"), ("KZT", "Казахстанский тенге"),
    ("TRY", "Турецкая лира"), ("AED", "Дирхам ОАЭ"), ("NGN", "Нигерийская найра"),
    ("INR", "Индийская рупия"), ("VND", "Вьетнамский донг"), ("BRL", "Бразильский реал"),
    ("ARS", "Аргентинское песо"), ("COP", "Колумбийское песо"), ("PEN", "Перуанский соль"),
    ("MXN", "Мексиканское песо"), ("CLP", "Чилийское песо"), ("ZAR", "Южноафриканский рэнд"),
    ("EGP", "Египетский фунт"), ("GHS", "Ганский седи"), ("KES", "Кенийский шиллинг"),
    ("MAD", "Марокканский дирхам"), ("PKR", "Пакистанская рупия"), ("BDT", "Бангладешская така"),
    ("LKR", "Шри-Ланкийская рупия"), ("IDR", "Индонезийская рупия"), ("THB", "Тайский бат"),
    ("MYR", "Малайзийский ринггит"), ("PHP", "Филиппинское песо"), ("KRW", "Южнокорейская вона"),
    ("TJS", "Таджикский сомони")
]
PAYMENT_METHODS = ["SBP", "Банковский перевод", "QIWI", "ЮMoney", "Tinkoff", "Monobank"]

# ——— Настройка БД ———
engine       = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ——— Модели ———
class User(Base):
    __tablename__ = "users"
    id      = Column(Integer, primary_key=True, index=True)
    uuid    = Column(String, unique=True, default=lambda: str(uuid4()))
    balance = Column(Float, default=0.0)

class Ad(Base):
    __tablename__ = "ads"
    id              = Column(Integer, primary_key=True, index=True)
    uuid            = Column(String, default=lambda: str(uuid4()), unique=True)
    type            = Column(String, nullable=False)         # buy/sell
    crypto          = Column(String, nullable=False)
    fiat            = Column(String, nullable=False)
    amount          = Column(Float, nullable=False)
    price           = Column(Float, nullable=False)
    min_limit       = Column(Float, nullable=False)
    max_limit       = Column(Float, nullable=False)
    payment_methods = Column(String, nullable=False)         # CSV
    created_at      = Column(DateTime, default=datetime.utcnow)
    trades          = relationship("Trade", back_populates="ad")

class Trade(Base):
    __tablename__ = "trades"
    id         = Column(Integer, primary_key=True, index=True)
    ad_id      = Column(Integer, ForeignKey("ads.id"))
    buyer_uuid = Column(String, nullable=False)
    status     = Column(String, default="pending")          # pending/paid/confirmed/disputed/canceled
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    ad         = relationship("Ad", back_populates="trades")
    messages   = relationship("Message", back_populates="trade", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id          = Column(Integer, primary_key=True, index=True)
    trade_id    = Column(Integer, ForeignKey("trades.id"))
    sender_uuid = Column(String, nullable=False)
    content     = Column(Text, nullable=False)
    timestamp   = Column(DateTime, default=datetime.utcnow)
    trade       = relationship("Trade", back_populates="messages")

class Operation(Base):
    __tablename__ = "operations"
    id         = Column(Integer, primary_key=True, index=True)
    user_uuid  = Column(String, index=True)
    type       = Column(String, nullable=False)             # deposit/withdraw
    amount     = Column(Float, nullable=False)
    address    = Column(String, nullable=True)
    status     = Column(String, default="pending")          # pending/completed
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ——— FastAPI setup ———
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY","secret123"))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ——— Утилиты ———
def get_user_uuid(request: Request):
    if not request.session.get("user_uuid"):
        request.session["user_uuid"] = str(uuid4())
    # ensure user row exists
    db = SessionLocal()
    u = db.query(User).filter(User.uuid==request.session["user_uuid"]).first()
    if not u:
        u = User(uuid=request.session["user_uuid"])
        db.add(u); db.commit()
    db.close()
    return request.session["user_uuid"]

def cancel_expired(db: Session):
    now = datetime.utcnow()
    for t in db.query(Trade).filter(Trade.status=="pending", Trade.expires_at<=now):
        t.status = "canceled"
    db.commit()

# ——— Маршруты ———
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/market")

@app.get("/market", response_class=HTMLResponse)
def market(request: Request, db: Session = Depends(get_db)):
    cancel_expired(db)
    user_uuid      = get_user_uuid(request)
    filtered_crypto= request.query_params.get("crypto","")
    filtered_fiat  = request.query_params.get("fiat","")
    filtered_pay   = request.query_params.get("payment","")

    q = db.query(Ad)
    if filtered_crypto: q = q.filter(Ad.crypto==filtered_crypto)
    if filtered_fiat:   q = q.filter(Ad.fiat==filtered_fiat)
    if filtered_pay:    q = q.filter(Ad.payment_methods.ilike(f"%{filtered_pay}%"))
    ads = q.all()

    return templates.TemplateResponse("market.html", {
        "request": request,
        "ads": ads,
        "user_uuid": user_uuid,
        "cryptos": CRYPTOS,
        "fiats": FIATS,
        "payments": PAYMENT_METHODS,
        "current_crypto": filtered_crypto,
        "current_fiat": filtered_fiat,
        "current_payment": filtered_pay
    })

@app.get("/create_ad", response_class=HTMLResponse)
def create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {
        "request": request,
        "cryptos": CRYPTOS,
        "fiats": FIATS,
        "payments": PAYMENT_METHODS
    })

@app.post("/create_ad")
def create_ad(
    request: Request,
    type: str = Form(...),
    crypto: str = Form(...),
    fiat: str = Form(...),
    amount: float = Form(...),
    price: float = Form(...),
    min_limit: float = Form(...),
    max_limit: float = Form(...),
    payment_methods: str = Form(...),
    db: Session = Depends(get_db)
):
    ad = Ad(
        type=type,
        crypto=crypto,
        fiat=fiat,
        amount=amount,
        price=price,
        min_limit=min_limit,
        max_limit=max_limit,
        payment_methods=payment_methods,
        created_at=datetime.utcnow()
    )
    db.add(ad); db.commit()
    return RedirectResponse("/market", status_code=302)

# … остальные маршруты (trade, profile, deposit, withdraw, admin) аналогично предыдущей версии …
