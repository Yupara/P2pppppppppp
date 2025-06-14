import os
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import (
    FastAPI,
    Request,
    Form,
    Depends,
    HTTPException
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# --- Настройка БД ---
DATABASE_URL = "sqlite:///./p2p.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Модели ---
class Ad(Base):
    __tablename__ = "ads"
    id              = Column(Integer, primary_key=True, index=True)
    uuid            = Column(String, default=lambda: str(uuid4()), unique=True)
    type            = Column(String, nullable=False)  # buy/sell
    crypto          = Column(String, nullable=False)
    fiat            = Column(String, nullable=False)
    amount          = Column(Float, nullable=False)
    price           = Column(Float, nullable=False)
    min_limit       = Column(Float, nullable=False)
    max_limit       = Column(Float, nullable=False)
    payment_methods = Column(String, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)

    trades = relationship("Trade", back_populates="ad")

class Trade(Base):
    __tablename__ = "trades"
    id         = Column(Integer, primary_key=True, index=True)
    ad_id      = Column(Integer, ForeignKey("ads.id"))
    buyer_uuid = Column(String, nullable=False)
    status     = Column(String, default="pending")  # pending, paid, confirmed, canceled, disputed
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    ad       = relationship("Ad", back_populates="trades")
    messages = relationship("Message", back_populates="trade", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id          = Column(Integer, primary_key=True, index=True)
    trade_id    = Column(Integer, ForeignKey("trades.id"))
    sender_uuid = Column(String, nullable=False)
    content     = Column(Text, nullable=False)
    timestamp   = Column(DateTime, default=datetime.utcnow)

    trade = relationship("Trade", back_populates="messages")

# создаём все таблицы
Base.metadata.create_all(bind=engine)

# --- FastAPI setup ---
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY","secret123"))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Утилиты ---
def get_user_uuid(request: Request):
    if not request.session.get("user_uuid"):
        request.session["user_uuid"] = str(uuid4())
    return request.session["user_uuid"]

def cancel_expired(db: Session):
    now = datetime.utcnow()
    expired = db.query(Trade).filter(
        Trade.status == "pending",
        Trade.expires_at <= now
    ).all()
    for t in expired:
        t.status = "canceled"
    db.commit()

# --- Маршруты ---
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/market")

@app.get("/market", response_class=HTMLResponse)
def market(
    request: Request,
    db: Session = Depends(get_db)
):
    cancel_expired(db)
    user_uuid = get_user_uuid(request)

    # фильтры из query params
    crypto = request.query_params.get("crypto", "")
    fiat   = request.query_params.get("fiat", "")
    payment= request.query_params.get("payment", "")

    query = db.query(Ad)
    if crypto:
        query = query.filter(Ad.crypto == crypto)
    if fiat:
        query = query.filter(Ad.fiat == fiat)
    if payment:
        query = query.filter(Ad.payment_methods.ilike(f"%{payment}%"))
    ads = query.all()

    # distinct для фильтров
    cryptos  = [r[0] for r in db.query(Ad.crypto).distinct()]
    fiats    = [r[0] for r in db.query(Ad.fiat).distinct()]
    payments = set()
    for pm, in db.query(Ad.payment_methods).distinct():
        for p in pm.split(","):
            payments.add(p.strip())

    return templates.TemplateResponse("market.html", {
        "request": request,
        "ads": ads,
        "user_uuid": user_uuid,
        "cryptos": cryptos,
        "fiats": fiats,
        "payments": sorted(payments),
        "current_crypto": crypto,
        "current_fiat": fiat,
        "current_payment": payment
    })

@app.get("/create_ad", response_class=HTMLResponse)
def create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

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
    db.add(ad)
    db.commit()
    return RedirectResponse("/market", status_code=302)

@app.get("/trade/create/{ad_id}")
def create_trade(
    ad_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    cancel_expired(db)
    ad = db.query(Ad).get(ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    user_uuid = get_user_uuid(request)
    trade = Trade(
        ad_id=ad.id,
        buyer_uuid=user_uuid,
        status="pending",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return RedirectResponse(f"/trade/{trade.id}", status_code=302)

@app.get("/trade/{trade_id}", response_class=HTMLResponse)
def view_trade(
    trade_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    cancel_expired(db)
    trade = db.query(Trade).get(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    user_uuid = get_user_uuid(request)
    is_buyer  = (trade.buyer_uuid == user_uuid)
    is_seller = (trade.ad.uuid == user_uuid)
    if not (is_buyer or is_seller):
        raise HTTPException(status_code=403, detail="Нет доступа")
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "trade": trade,
        "messages": trade.messages,
        "is_buyer": is_buyer,
        "is_seller": is_seller,
        "now": datetime.utcnow().isoformat()
    })

@app.post("/trade/{trade_id}/paid")
def mark_paid(
    trade_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    t = db.query(Trade).get(trade_id)
    user_uuid = get_user_uuid(request)
    if not t or t.buyer_uuid != user_uuid or t.status != "pending":
        raise HTTPException(status_code=403, detail="Невозможно оплатить")
    t.status = "paid"
    db.commit()
    return RedirectResponse(f"/trade/{trade_id}", status_code=302)

@app.post("/trade/{trade_id}/confirm")
def mark_confirm(
    trade_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    t = db.query(Trade).get(trade_id)
    user_uuid = get_user_uuid(request)
    if not t or t.ad.uuid != user_uuid or t.status != "paid":
        raise HTTPException(status_code=403, detail="Невозможно подтвердить")
    t.status = "confirmed"
    db.commit()
    return RedirectResponse(f"/trade/{trade_id}", status_code=302)

@app.post("/trade/{trade_id}/dispute")
def mark_dispute(
    trade_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    t = db.query(Trade).get(trade_id)
    user_uuid = get_user_uuid(request)
    if not t or user_uuid not in (t.buyer_uuid, t.ad.uuid):
        raise HTTPException(status_code=403, detail="Нет доступа")
    t.status = "disputed"
    db.commit()
    return RedirectResponse(f"/trade/{trade_id}", status_code=302)

@app.post("/trade/{trade_id}/message")
def send_message(
    trade_id: int,
    request: Request,
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    t = db.query(Trade).get(trade_id)
    user_uuid = get_user_uuid(request)
    if not t or user_uuid not in (t.buyer_uuid, t.ad.uuid):
        raise HTTPException(status_code=403, detail="Нет доступа")
    msg = Message(
        trade_id=trade_id,
        sender_uuid=user_uuid,
        content=content,
        timestamp=datetime.utcnow()
    )
    db.add(msg)
    db.commit()
    return RedirectResponse(f"/trade/{trade_id}", status_code=302)
