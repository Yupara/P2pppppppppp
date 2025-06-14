# app.py
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

import stripe

# ——— ЗАГРУЗКА ОКРУЖЕНИЯ ———
load_dotenv()
stripe.api_key         = os.getenv("STRIPE_API_KEY")
WEBHOOK_SECRET         = os.getenv("STRIPE_WEBHOOK_SECRET")
DOMAIN                 = os.getenv("YOUR_DOMAIN", "http://localhost:8000")

# ——— КОНСТАНТЫ ———
ADMIN_UUID             = "293dd908-eac9-4082-b5e6-112d649a60bc"

# ——— БД ———
DATABASE_URL           = "sqlite:///./p2p.db"
engine                 = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal           = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base                   = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ——— МОДЕЛИ ———
class User(Base):
    __tablename__ = "users"
    id       = Column(Integer, primary_key=True, index=True)
    uuid     = Column(String, unique=True, default=lambda: str(uuid4()))
    balance  = Column(Float, default=0.0)

class Ad(Base):
    __tablename__ = "ads"
    id              = Column(Integer, primary_key=True, index=True)
    uuid            = Column(String, unique=True, default=lambda: str(uuid4()))
    type            = Column(String)  # buy/sell
    crypto          = Column(String)
    fiat            = Column(String)
    amount          = Column(Float)
    price           = Column(Float)
    min_limit       = Column(Float)
    max_limit       = Column(Float)
    payment_methods = Column(String)
    created_at      = Column(DateTime, default=datetime.utcnow)
    trades          = relationship("Trade", back_populates="ad")

class Trade(Base):
    __tablename__ = "trades"
    id         = Column(Integer, primary_key=True, index=True)
    ad_id      = Column(Integer, ForeignKey("ads.id"))
    buyer_uuid = Column(String)
    status     = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    ad         = relationship("Ad", back_populates="trades")
    messages   = relationship("Message", back_populates="trade", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id          = Column(Integer, primary_key=True, index=True)
    trade_id    = Column(Integer, ForeignKey("trades.id"))
    sender_uuid = Column(String)
    content     = Column(Text)
    timestamp   = Column(DateTime, default=datetime.utcnow)
    trade       = relationship("Trade", back_populates="messages")

class Operation(Base):
    __tablename__ = "operations"
    id         = Column(Integer, primary_key=True, index=True)
    user_uuid  = Column(String)
    type       = Column(String)    # deposit / withdraw
    amount     = Column(Float)
    address    = Column(String)
    status     = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    id             = Column(Integer, primary_key=True, index=True)
    user_uuid      = Column(String)
    stripe_session = Column(String, unique=True)
    amount         = Column(Float)
    currency       = Column(String, default="usd")
    status         = Column(String, default="created")
    created_at     = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ——— FASTAPI ———
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY","secret123"))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ——— УТИЛИТЫ ———
def get_user_uuid(request: Request):
    if not request.session.get("user_uuid"):
        request.session["user_uuid"] = str(uuid4())
    # ensure User record
    db = SessionLocal(); uu = request.session["user_uuid"]
    if not db.query(User).filter(User.uuid==uu).first():
        db.add(User(uuid=uu)); db.commit()
    db.close()
    return request.session["user_uuid"]

def cancel_expired(db: Session):
    now = datetime.utcnow()
    for t in db.query(Trade).filter(Trade.status=="pending", Trade.expires_at<=now):
        t.status = "canceled"
    db.commit()

# ——— МАРШРУТЫ ———

@app.get("/", include_in_schema=False)
def root(): return RedirectResponse("/market")

# ----- РЫНОК -----
@app.get("/market", response_class=HTMLResponse)
def market(request: Request, db: Session = Depends(get_db)):
    cancel_expired(db)
    uu = get_user_uuid(request)
    # фильтры
    crypto = request.query_params.get("crypto","")
    fiat   = request.query_params.get("fiat","")
    paym   = request.query_params.get("payment","")
    q = db.query(Ad)
    if crypto: q=q.filter(Ad.crypto==crypto)
    if fiat:   q=q.filter(Ad.fiat==fiat)
    if paym:   q=q.filter(Ad.payment_methods.ilike(f"%{paym}%"))
    ads = q.all()
    cryptos  = [r[0] for r in db.query(Ad.crypto).distinct()]
    fiats    = [r[0] for r in db.query(Ad.fiat).distinct()]
    payments = set()
    for pm, in db.query(Ad.payment_methods).distinct():
        payments |= set(p.strip() for p in pm.split(","))
    return templates.TemplateResponse("market.html", {
        "request": request, "ads": ads, "user_uuid": uu,
        "cryptos": cryptos, "fiats": fiats, "payments":sorted(payments),
        "current_crypto":crypto,"current_fiat":fiat,"current_payment":paym
    })

# ----- СОЗДАНИЕ ОБЪЯВЛЕНИЯ -----
@app.get("/create_ad", response_class=HTMLResponse)
def create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html",{"request":request})

@app.post("/create_ad")
def create_ad(request: Request,
    type: str=Form(...), crypto: str=Form(...), fiat: str=Form(...),
    amount: float=Form(...), price: float=Form(...),
    min_limit: float=Form(...), max_limit: float=Form(...),
    payment_methods: str=Form(...),
    db: Session=Depends(get_db)
):
    db.add(Ad(
      type=type,crypto=crypto,fiat=fiat,amount=amount,price=price,
      min_limit=min_limit,max_limit=max_limit,
      payment_methods=payment_methods,created_at=datetime.utcnow()
    ))
    db.commit()
    return RedirectResponse("/market",302)

# ----- СДЕЛКА -----
@app.get("/trade/create/{ad_id}")
def create_trade(ad_id:int, request:Request, db:Session=Depends(get_db)):
    cancel_expired(db)
    ad=db.query(Ad).get(ad_id)
    if not ad: raise HTTPException(404)
    uu=get_user_uuid(request)
    t=Trade(ad_id=ad_id,buyer_uuid=uu,status="pending",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow()+timedelta(minutes=30))
    db.add(t); db.commit(); db.refresh(t)
    return RedirectResponse(f"/trade/{t.id}",302)

@app.get("/trade/{trade_id}", response_class=HTMLResponse)
def view_trade(trade_id:int,request:Request,db:Session=Depends(get_db)):
    cancel_expired(db)
    t=db.query(Trade).get(trade_id)
    if not t: raise HTTPException(404)
    uu=get_user_uuid(request)
    is_buyer = (t.buyer_uuid==uu)
    is_seller= (t.ad.uuid==uu)
    if not (is_buyer or is_seller): raise HTTPException(403)
    return templates.TemplateResponse("trade.html", {
        "request":request,"trade":t,"messages":t.messages,
        "is_buyer":is_buyer,"is_seller":is_seller,
        "now":datetime.utcnow().isoformat()
    })

@app.post("/trade/{trade_id}/paid")
def mark_paid(trade_id:int,request:Request,db:Session=Depends(get_db)):
    t=db.query(Trade).get(trade_id); uu=get_user_uuid(request)
    if not t or t.buyer_uuid!=uu or t.status!="pending": raise HTTPException(403)
    t.status="paid"; db.commit()
    return RedirectResponse(f"/trade/{trade_id}",302)

@app.post("/trade/{trade_id}/confirm")
def mark_confirm(trade_id:int,request:Request,db:Session=Depends(get_db)):
    t=db.query(Trade).get(trade_id); uu=get_user_uuid(request)
    if not t or t.ad.uuid!=uu or t.status!="paid": raise HTTPException(403)
    t.status="confirmed"; db.commit()
    return RedirectResponse(f"/trade/{trade_id}",302)

@app.post("/trade/{trade_id}/dispute")
def mark_dispute(trade_id:int,request:Request,db:Session=Depends(get_db)):
    t=db.query(Trade).get(trade_id); uu=get_user_uuid(request)
    if not t or uu not in (t.buyer_uuid,t.ad.uuid): raise HTTPException(403)
    t.status="disputed"; db.commit()
    return RedirectResponse(f"/trade/{trade_id}",302)

@app.post("/trade/{trade_id}/message")
def send_message(trade_id:int,request:Request,content:str=Form(...),db:Session=Depends(get_db)):
    t=db.query(Trade).get(trade_id); uu=get_user_uuid(request)
    if not t or uu not in (t.buyer_uuid,t.ad.uuid): raise HTTPException(403)
    db.add(Message(trade_id=trade_id,sender_uuid=uu,content=content,timestamp=datetime.utcnow()))
    db.commit()
    return RedirectResponse(f"/trade/{trade_id}",302)

# ----- ПРОФИЛЬ -----
@app.get("/profile", response_class=HTMLResponse)
def profile(request:Request,db:Session=Depends(get_db)):
    uu=get_user_uuid(request)
    buys=db.query(Trade).filter(Trade.buyer_uuid==uu).all()
    sells=db.query(Trade).join(Ad).filter(Ad.uuid==uu).all()
    user=db.query(User).filter(User.uuid==uu).first()
    ops=db.query(Operation).filter(Operation.user_uuid==uu).order_by(Operation.created_at.desc()).all()
    return templates.TemplateResponse("profile.html", {
        "request":request,"buys":buys,"sells":sells,"user":user,"ops":ops
    })

# ----- ПОПОЛНЕНИЕ / ВЫВОД -----
@app.get("/deposit", response_class=HTMLResponse)
def deposit_form(request:Request):
    return templates.TemplateResponse("deposit.html",{"request":request})

@app.post("/deposit")
def deposit(request:Request,amount:float=Form(...),db:Session=Depends(get_db)):
    uu=get_user_uuid(request)
    addr=str(uuid4())
    db.add(Operation(user_uuid=uu,type="deposit",amount=amount,address=addr,status="pending"))
    db.commit()
    return RedirectResponse("/profile",302)

@app.get("/withdraw", response_class=HTMLResponse)
def withdraw_form(request:Request):
    return templates.TemplateResponse("withdraw.html",{"request":request})

@app.post("/withdraw")
def withdraw(request:Request,amount:float=Form(...),address:str=Form(...),db:Session=Depends(get_db)):
    uu=get_user_uuid(request); user=db.query(User).filter(User.uuid==uu).first()
    if user.balance<amount: raise HTTPException(400,"Недостаточно средств")
    user.balance-=amount
    db.add(Operation(user_uuid=uu,type="withdraw",amount=amount,address=address,status="pending"))
    db.commit()
    return RedirectResponse("/profile",302)

# ----- STRIPE -----
@app.post("/payment/create-session")
def create_payment_session(request:Request,amount:float=Form(...),db:Session=Depends(get_db)):
    uu=get_user_uuid(request); stripe_amount=int(amount*100)
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price_data":{
            "currency":"usd",
            "product_data":{"name":"Пополнение USDT"},
            "unit_amount":stripe_amount
        },"quantity":1}],
        mode="payment",
        success_url=f"{DOMAIN}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{DOMAIN}/profile"
    )
    db.add(PaymentTransaction(user_uuid=uu,stripe_session=session.id,amount=amount))
    db.commit()
    return JSONResponse({"checkout_url":session.url})

@app.post("/webhook")
async def stripe_webhook(request:Request,db:Session=Depends(get_db)):
    payload=await request.body(); sig=request.headers.get("stripe-signature")
    try:
        evt=stripe.Webhook.construct_event(payload,sig,WEBHOOK_SECRET)
    except:
        raise HTTPException(400,"Invalid signature")
    if evt["type"]=="checkout.session.completed":
        sess=evt["data"]["object"]; tx=db.query(PaymentTransaction).filter_by(stripe_session=sess["id"]).first()
        if tx and tx.status=="created":
            tx.status="completed"
            u=db.query(User).filter(User.uuid==tx.user_uuid).first()
            if u: u.balance+=tx.amount
            db.commit()
    return {"status":"ok"}

@app.get("/payment/success", response_class=HTMLResponse)
def payment_success(request:Request):
    return templates.TemplateResponse("payment_success.html",{"request":request})

@app.get("/payment/cancel", response_class=HTMLResponse)
def payment_cancel(request:Request):
    return templates.TemplateResponse("payment_cancel.html",{"request":request})

# ----- АДМИН -----
@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request:Request,db:Session=Depends(get_db)):
    uu=get_user_uuid(request)
    if uu!=ADMIN_UUID: raise HTTPException(403,"Доступ запрещён")
    stats={
      "total_ads":db.query(Ad).count(),
      "total_trades":db.query(Trade).count(),
      "pending":db.query(Trade).filter(Trade.status=="pending").count(),
      "disputes":db.query(Trade).filter(Trade.status=="disputed").count()
    }
    return templates.TemplateResponse("admin.html",{"request":request,**stats})
