from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pytz

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Database setup
engine = create_engine('sqlite:///p2p_exchange.db', echo=True)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    orders_completed = Column(Integer, default=0)
    last_seen = Column(DateTime, default=datetime.utcnow)
    rating = Column(Float, default=99.0)
    completion_rate = Column(Float, default=100.0)
    avg_transfer_time = Column(String, default="2 мин.")
    offers = relationship("Offer", back_populates="user")

class Offer(Base):
    __tablename__ = 'offers'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    offer_type = Column(String)
    currency = Column(String)
    amount = Column(Float)
    fiat = Column(String)
    fiat_amount = Column(Float)
    payment_method = Column(String)
    contact = Column(String)
    payment_window = Column(Integer)
    only_verified = Column(Boolean, default=False)
    only_vip = Column(Boolean, default=False)
    description = Column(String)
    user = relationship("User", back_populates="offers")

Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Add or get test user
def add_or_get_test_user():
    user = db.query(User).filter(User.email == "testuser@example.com").first()
    if not user:
        user = User(email="testuser@example.com", orders_completed=0, last_seen=datetime.utcnow())
        db.add(user)
        db.commit()
    return user

# Add test data
def add_test_data():
    if not db.query(Offer).first():
        user1 = User(email="user1@example.com", orders_completed=2426, last_seen=datetime.utcnow())
        user2 = User(email="user2@example.com", orders_completed=1500, last_seen=datetime.utcnow() - timedelta(minutes=20))
        db.add(user1)
        db.add(user2)
        db.commit()
        offer1 = Offer(user_id=1, offer_type="sell", currency="USDT", amount=140.0, fiat="RUB", fiat_amount=140 * 77.10, payment_method="Sberbank", contact="user1_contact", payment_window=30)
        offer2 = Offer(user_id=2, offer_type="buy", currency="BTC", amount=0.5, fiat="USD", fiat_amount=0.5 * 60000, payment_method="PayPal", contact="user2_contact", payment_window=15)
        db.add(offer1)
        db.add(offer2)
        db.commit()

add_test_data()

# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, tab: str = "buy", currency: str = None, fiat: str = None, amount: float = None, payment_method: str = None, only_verified: bool = False, only_online: bool = False, only_merchants: bool = False):
    try:
        offers = db.query(Offer).filter(Offer.offer_type == ("sell" if tab == "buy" else "buy"))
        if currency:
            offers = offers.filter(Offer.currency == currency)
        if fiat:
            offers = offers.filter(Offer.fiat == fiat)
        if amount:
            offers = offers.filter(Offer.amount >= amount)
        if payment_method:
            offers = offers.filter(Offer.payment_method == payment_method)
        if only_verified:
            offers = offers.filter(Offer.only_verified == True)
        if only_online:
            offers = offers.join(User).filter(User.last_seen > datetime.utcnow() - timedelta(minutes=15))
        if only_merchants:
            offers = offers.filter(Offer.only_vip == True)
        offers = offers.all()
        now = datetime.now(pytz.timezone('Asia/Dushanbe'))
        return templates.TemplateResponse("index.html", {"request": request, "offers": offers, "tab": tab, "currency": currency, "fiat": fiat, "amount": amount, "payment_method": payment_method, "only_verified": only_verified, "only_online": only_online, "only_merchants": only_merchants, "now": now})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering index page: {str(e)}")

@app.get("/offers/filter", response_class=HTMLResponse)
async def filter_offers(request: Request, offer_type: str, currency: str = None, fiat: str = None, amount: float = None, payment_method: str = None, only_verified: bool = False, only_online: bool = False, only_merchants: bool = False):
    tab = "buy" if offer_type == "buy" else "sell"
    url = f"/?tab={tab}"
    if currency:
        url += f"&currency={currency}"
    if fiat:
        url += f"&fiat={fiat}"
    if amount:
        url += f"&amount={amount}"
    if payment_method:
        url += f"&payment_method={payment_method}"
    if only_verified:
        url += f"&only_verified={only_verified}"
    if only_online:
        url += f"&only_online={only_online}"
    if only_merchants:
        url += f"&only_merchants={only_merchants}"
    return RedirectResponse(url)

@app.post("/create-offer")
async def create_offer(offer_type: str = Form(...), currency: str = Form(...), amount: float = Form(...), fiat: str = Form(...), fiat_amount: float = Form(...), payment_method: str = Form(...), contact: str = Form(...), payment_window: int = Form(...), only_verified: bool = Form(False), only_vip: bool = Form(False), description: str = Form(None)):
    try:
        user = add_or_get_test_user()
        new_offer = Offer(user_id=user.id, offer_type=offer_type, currency=currency, amount=amount, fiat=fiat, fiat_amount=fiat_amount, payment_method=payment_method, contact=contact, payment_window=payment_window, only_verified=only_verified, only_vip=only_vip, description=description)
        db.add(new_offer)
        db.commit()
        return RedirectResponse("/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating offer: {str(e)}")

@app.get("/buy-sell/{offer_id}", response_class=HTMLResponse)
async def buy_sell_page(request: Request, offer_id: int):
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        now = datetime.now(pytz.timezone('Asia/Dushanbe'))
        return templates.TemplateResponse("buy_sell.html", {"request": request, "offer": offer, "now": now})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering buy/sell page: {str(e)}")

@app.post("/buy-offer/{offer_id}")
async def buy_offer(offer_id: int):
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        user = offer.user
        user.orders_completed += 1
        db.delete(offer)
        db.commit()
        return RedirectResponse("/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error buying offer: {str(e)}")

@app.get("/orders", response_class=HTMLResponse)
async def orders(request: Request):
    return templates.TemplateResponse("orders.html", {"request": request})

@app.get("/ads", response_class=HTMLResponse)
async def ads(request: Request):
    return templates.TemplateResponse("ads.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/profile/{user_id}", response_class=HTMLResponse)
async def user_profile(request: Request, user_id: int):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return templates.TemplateResponse("profile.html", {"request": request, "user": user})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering profile page: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
