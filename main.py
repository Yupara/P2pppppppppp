from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

DATABASE_URL = "sqlite:///p2p_exchange.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True)
    balance = Column(Float, default=0.0)
    verified = Column(Boolean, default=False)
    notifications_enabled = Column(Boolean, default=True)
    subscriptions_enabled = Column(Boolean, default=True)

class Offer(Base):
    __tablename__ = "offers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    offer_type = Column(String)
    currency = Column(String)
    amount = Column(Float)
    fiat = Column(String)
    fiat_amount = Column(Float)
    payment_method = Column(String)
    contact = Column(String)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def add_test_data():
    db = SessionLocal()
    try:
        test_user = db.query(User).filter(User.id == 1).first()
        if not test_user:
            new_user = User(id=1, email="para1333@example.com", phone="1234567890", balance=70.96, verified=True)
            db.add(new_user)
        other_user = db.query(User).filter(User.id == 2).first()
        if not other_user:
            other_user = User(id=2, email="user2@example.com", phone="0987654321", balance=100.0, verified=True)
            db.add(other_user)
        offer = db.query(Offer).filter(Offer.user_id == 2).first()
        if not offer:
            new_offer = Offer(user_id=2, offer_type="sell", currency="USDT", amount=1000.0, fiat="RUB", fiat_amount=95000.0, payment_method="SBP", contact="user2_contact")
            db.add(new_offer)
        db.commit()
    finally:
        db.close()

add_test_data()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == 1).first()
        offers = db.query(Offer).filter(Offer.user_id == 1, Offer.status == "active").all()
        other_offers = db.query(Offer).filter(Offer.user_id != 1, Offer.status == "active").all()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "user": user,
            "offers": offers,
            "other_offers": other_offers
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == 1).first()
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "user": user
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update-settings")
async def update_settings(notifications_enabled: bool = Form(False), subscriptions_enabled: bool = Form(False)):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == 1).first()
        user.notifications_enabled = notifications_enabled
        user.subscriptions_enabled = subscriptions_enabled
        db.commit()
        return {"message": "Settings updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-offer")
async def create_offer(offer_type: str = Form(...), currency: str = Form(...), amount: float = Form(...), fiat: str = Form(...), fiat_amount: float = Form(...), payment_method: str = Form(...), contact: str = Form(...)):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == 1).first()
        if not user or user.balance < amount or amount < 500 or amount > 5000:
            raise HTTPException(status_code=400, detail="Insufficient balance or amount out of range (500-5000)")
        user.balance -= amount
        offer = Offer(user_id=1, offer_type=offer_type, currency=currency, amount=amount, fiat=fiat, fiat_amount=fiat_amount, payment_method=payment_method, contact=contact)
        db.add(offer)
        db.commit()
        return {"message": "Offer created", "balance": user.balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/deposit")
async def deposit(amount: float = Form(...)):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == 1).first()
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")
        user.balance += amount
        db.commit()
        return {"message": "Deposit successful", "balance": user.balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
