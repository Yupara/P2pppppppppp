from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os

from models import Base, User, Ad, Message

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_URL = f"sqlite:///{os.path.join(BASE_DIR, 'db.sqlite3')}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def create_test_user():
    db = SessionLocal()
    if not db.query(User).filter_by(username="seller123").first():
        user = User(username="seller123", hashed_password="123456")
        db.add(user)
        db.commit()
    db.close()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/market", response_class=HTMLResponse)
def market(request: Request, db: Session = Depends(get_db)):
    ads = db.query(Ad).all()
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

@app.get("/create", response_class=HTMLResponse)
def create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create", response_class=RedirectResponse)
def create_ad(
    request: Request,
    type: str = Form(...),
    currency: str = Form(...),
    price: float = Form(...),
    amount: float = Form(...),
    payment_method: str = Form(...),
    db: Session = Depends(get_db),
):
    ad = Ad(
        type=type,
        currency=currency,
        price=price,
        amount=amount,
        payment_method=payment_method,
        owner="seller123",  # временно
    )
    db.add(ad)
    db.commit()
    return RedirectResponse(url="/market", status_code=303)

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade(ad_id: int, request: Request, db: Session = Depends(get_db)):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        return templates.TemplateResponse("index.html", {"request": request, "message": "Объявление не найдено"})
    
    end_time = datetime.utcnow() + timedelta(minutes=15)
    messages = db.query(Message).filter(Message.trade_id == ad_id).order_by(Message.timestamp).all()

    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "end_time": end_time.strftime('%Y-%m-%dT%H:%M:%S'),
        "messages": messages
    })

@app.post("/trade/{ad_id}/send", response_class=RedirectResponse)
def send_message(ad_id: int, request: Request, message: str = Form(...), db: Session = Depends(get_db)):
    sender = "Покупатель"
    new_msg = Message(trade_id=ad_id, sender=sender, content=message)
    db.add(new_msg)
    db.commit()
    return RedirectResponse(f"/trade/{ad_id}", status_code=303)
