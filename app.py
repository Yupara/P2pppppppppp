# app.py

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# ================= Database Setup =================

DATABASE_URL = "sqlite:///./p2p.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False
)
Base = declarative_base()

# ================= Models =================

class User(Base):
    __tablename__ = "users"
    id       = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    balance  = Column(Float, default=0.0)

class Ad(Base):
    __tablename__ = "ads"
    id      = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type    = Column(String, nullable=False)  # "buy" или "sell"
    amount  = Column(Float, nullable=False)
    price   = Column(Float, nullable=False)
    user    = relationship("User")

class Order(Base):
    __tablename__ = "orders"
    id       = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    ad_id    = Column(Integer, ForeignKey("ads.id"))
    amount   = Column(Float, nullable=False)
    status   = Column(String, default="waiting")
    buyer    = relationship("User", foreign_keys=[buyer_id])
    ad       = relationship("Ad")

class Message(Base):
    __tablename__ = "messages"
    id        = Column(Integer, primary_key=True, index=True)
    order_id  = Column(Integer, ForeignKey("orders.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    text      = Column(String, nullable=False)
    order     = relationship("Order")
    sender    = relationship("User")

Base.metadata.create_all(bind=engine)

# ================= FastAPI Setup =================

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="CHANGE_ME_TO_RANDOM_SECRET")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ================= Dependencies =================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Не авторизован")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    return user

# Админ — первый зарегистрировавшийся (ID=1) получает комиссию
admin_user_id = 1

# ================= Routes =================

@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse(url="/market", status_code=302)

@app.get("/market", response_class=HTMLResponse)
def market(request: Request, db: Session = Depends(get_db)):
    ads = db.query(Ad).all()
    return templates.TemplateResponse("market.html", {
        "request": request,
        "ads": ads
    })

@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@app.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Имя пользователя занято"
        })
    user = User(username=username, password=password)
    db.add(user)
    db.commit()
    return RedirectResponse(url="/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter_by(username=username, password=password).first()
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Неверный логин или пароль"
        })
    request.session["user_id"] = user.id
    return RedirectResponse(url="/market", status_code=302)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)

@app.get("/create_ad", response_class=HTMLResponse)
def create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create_ad")
def create_ad(
    request: Request,
    type: str = Form(...),
    amount: float = Form(...),
    price: float = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    ad = Ad(user_id=user.id, type=type, amount=amount, price=price)
    db.add(ad)
    db.commit()
    return RedirectResponse(url="/market", status_code=302)

@app.get("/create_order/{ad_id}")
def create_order(
    ad_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad or ad.user_id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Нельзя создать эту сделку")
    order = Order(buyer_id=user.id, ad_id=ad.id, amount=ad.amount)
    db.add(order)
    db.commit()
    return RedirectResponse(url=f"/trade/{order.id}", status_code=302)

@app.get("/trade/{order_id}", response_class=HTMLResponse)
def trade_page(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    order = db.query(Order).filter(Order.id == order_id).first()
    messages = db.query(Message).filter(Message.order_id == order_id).all()
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "order": order,
        "messages": messages,
        "user": user
    })

@app.post("/message/{order_id}")
def send_message(
    request: Request,
    order_id: int,
    text: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    msg = Message(order_id=order_id, sender_id=user.id, text=text)
    db.add(msg)
    db.commit()
    return RedirectResponse(url=f"/trade/{order_id}", status_code=302)

@app.post("/pay/{order_id}")
def pay_order(
    request: Request,
    order_id: int,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or order.buyer_id != user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Нельзя оплатить")
    order.status = "paid"
    db.commit()
    return RedirectResponse(url=f"/trade/{order_id}", status_code=302)

@app.post("/confirm/{order_id}")
def confirm_order(
    request: Request,
    order_id: int,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or order.ad.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Нельзя подтвердить")
    buyer = db.query(User).filter(User.id == order.buyer_id).first()
    seller = user
    admin  = db.query(User).filter(User.id == admin_user_id).first()

    commission    = order.amount * 0.005
    seller_amount = order.amount - commission

    if seller.balance < order.amount:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Недостаточно средств")
    seller.balance -= order.amount
    buyer.balance  += seller_amount
    if admin:
        admin.balance += commission

    order.status = "confirmed"
    db.commit()
    return RedirectResponse(url="/orders/mine", status_code=302)

@app.get("/orders/mine", response_class=HTMLResponse)
def my_orders(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    orders = db.query(Order).filter(
        (Order.buyer_id == user.id) | (Order.ad.has(user_id=user.id))
    ).all()
    return templates.TemplateResponse("orders.html", {
        "request": request, "orders": orders
    })

@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse("profile.html", {
        "request": request, "user": user
    })
