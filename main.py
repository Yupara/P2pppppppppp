from fastapi import FastAPI, Request, Form, HTTPException
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

load_dotenv()

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
    vip_level = Column(Integer, default=0)
    vip_progress = Column(Float, default=0.0)
    total_invested = Column(Float, default=0.0)

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
            new_user = User(id=1, email="test@example.com", phone="1234567890", balance=1000.0)
            db.add(new_user)
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
        offers = db.query(Offer).filter(Offer.status == "active").all()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "user": user,
            "offers": offers
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/invest")
async def invest(amount: float = Form(...)):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == 1).first()
        if not user or user.balance < amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        user.balance -= amount
        user.total_invested += amount
        user.vip_progress += amount / 50000.0 * 100  # 50,000 USD for next VIP level
        if user.vip_progress >= 100:
            user.vip_level += 1
            user.vip_progress = 0.0
        db.commit()
        return {"message": "Investment successful", "balance": user.balance, "vip_level": user.vip_level, "vip_progress": user.vip_progress}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-offer")
async def create_offer(offer_type: str = Form(...), currency: str = Form(...), amount: float = Form(...), fiat: str = Form(...), fiat_amount: float = Form(...), payment_method: str = Form(...), contact: str = Form(...)):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == 1).first()
        if not user or user.balance < amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        user.balance -= amount
        offer = Offer(user_id=1, offer_type=offer_type, currency=currency, amount=amount, fiat=fiat, fiat_amount=fiat_amount, payment_method=payment_method, contact=contact)
        db.add(offer)
        db.commit()
        return {"message": "Offer created", "balance": user.balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
