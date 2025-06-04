from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
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
    balance = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    order_type = Column(String)  # "buy" или "sell"
    currency = Column(String)    # "USDT"
    amount = Column(Float)
    fiat = Column(String)        # "RUB"
    fiat_amount = Column(Float)
    payment_method = Column(String)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def add_test_data():
    db = SessionLocal()
    try:
        test_user = db.query(User).filter(User.id == 1).first()
        if not test_user:
            new_user = User(id=1, email="test@example.com", balance=1000.0)
            db.add(new_user)
        test_order = db.query(Order).filter(Order.id == 1).first()
        if not test_order:
            new_order = Order(
                id=1,
                user_id=1,
                order_type="sell",
                currency="USDT",
                amount=100.0,
                fiat="RUB",
                fiat_amount=9500.0,
                payment_method="Local Card"
            )
            db.add(new_order)
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
        orders = db.query(Order).filter(Order.status == "active").all()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "user": user,
            "orders": orders
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-order")
async def create_order(order_type: str = Form(...), amount: float = Form(...), fiat_amount: float = Form(...), payment_method: str = Form(...)):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == 1).first()
        if order_type == "sell" and user.balance < amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        if order_type == "sell":
            user.balance -= amount
        order = Order(
            user_id=1,
            order_type=order_type,
            currency="USDT",
            amount=amount,
            fiat="RUB",
            fiat_amount=fiat_amount,
            payment_method=payment_method
        )
        db.add(order)
        db.commit()
        return {"message": "Order created", "balance": user.balance}
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
