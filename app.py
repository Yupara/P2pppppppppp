# app.py
from fastapi import (
    FastAPI, Request, Form, Depends,
    HTTPException, status
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

from uuid import uuid4

# —— Database setup ——
DATABASE_URL = "sqlite:///./p2p.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# —— Models ——
class User(Base):
    __tablename__ = "users"
    id       = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    balance  = Column(Float, default=0.0)

class Ad(Base):
    __tablename__ = "ads"
    id      = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type    = Column(String)   # "buy" или "sell"
    amount  = Column(Float)
    price   = Column(Float)
    user    = relationship("User")

class Order(Base):
    __tablename__ = "orders"
    id       = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    ad_id    = Column(Integer, ForeignKey("ads.id"))
    amount   = Column(Float)
    status   = Column(String, default="waiting")  # waiting, paid, confirmed
    buyer    = relationship("User", foreign_keys=[buyer_id])
    ad       = relationship("Ad")

class Message(Base):
    __tablename__ = "messages"
    id        = Column(Integer, primary_key=True, index=True)
    order_id  = Column(Integer, ForeignKey("orders.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    text      = Column(String)
    order     = relationship("Order")
    sender    = relationship("User")

Base.metadata.create_all(bind=engine)

# —— App, templates, static ——
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="CHANGE_THIS_SECRET")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# —— Dependencies ——
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Не авторизован")
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Пользователь не найден")
    return user

# —— Admin commission settings ——
admin_user_id = 1  # при первом запуске зарегистрируйте админа, чтобы он получил ID=1

# —— Routes —— 

@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse("/market", status_code=302)

# — Market (публичный) —
@app.get("/market", response_class=HTMLResponse)
def market(request: Request, db: Session = Depends(get_db)):
    ads = db.query(Ad).all()
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

# — Registration —
@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@app.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(User).filter_by(username=username).first():
        return templates.TemplateResponse("register.html", {
            "request": request, "error": "Имя пользователя занято"
        })
    user = User(username=username, password=password, balance=0.0)
    db.add(user)
    db.commit()
    request.session["user_id"] = user.id
    return RedirectResponse("/market", status_code=302)

# — Login —
@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter_by(username=username, password=password).first()
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request, "error": "Неверные учётные данные"
        })
    request.session["user_id"] = user.id
    return RedirectResponse("/market", status_code=302)

# — Logout —
@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)

# — Create Ad —
@app.get("/create_ad", response_class=HTMLResponse)
def create_ad_form(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create_ad")
def create_ad(
    request: Request,
    type: str = Form(...),
    amount: float = Form(...),
    price: float = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    ad = Ad(user_id=user.id, type=type, amount=amount, price=price)
    db.add(ad)
    db.commit()
    return RedirectResponse("/market", status_code=302)

# — Create Order —
@app.get("/create_order/{ad_id}")
def create_order(
    ad_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    ad = db.query(Ad).get(ad_id)
    if not ad:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Объявление не найдено")
    if ad.user_id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Нельзя купить у себя")
    order = Order(buyer_id=user.id, ad_id=ad.id, amount=ad.amount, status="waiting")
    db.add(order)
    db.commit()
    return RedirectResponse(f"/trade/{order.id}", status_code=302)

# — Trade view —
@app.get("/trade/{order_id}", response_class=HTMLResponse)
def trade_view(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Сделка не найдена")
    messages = db.query(Message).filter_by(order_id=order.id).all()
    return templates.TemplateResponse("trade.html", {
        "request": request, "order": order,
        "messages": messages, "user": user
    })

# — Mark paid —
@app.post("/pay/{order_id}")
def pay_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    order = db.query(Order).get(order_id)
    if not order or order.buyer_id != user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Нельзя оплатить")
    order.status = "paid"
    db.commit()
    return RedirectResponse(f"/trade/{order.id}", status_code=302)

# — Confirm & commission to admin —
@app.post("/confirm/{order_id}")
def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Сделка не найдена")
    ad = order.ad
    seller = db.query(User).get(ad.user_id)
    buyer  = db.query(User).get(order.buyer_id)
    admin  = db.query(User).get(admin_user_id)

    if seller.id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Вы не продавец")
    if order.status != "paid":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Сначала отметьте оплату")

    commission    = order.amount * 0.005
    seller_amount = order.amount - commission

    if seller.balance < order.amount:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Недостаточно баланса у продавца")

    seller.balance -= order.amount
    buyer.balance  += seller_amount
    if admin:
        admin.balance += commission

    order.status = "confirmed"
    db.commit()
    return RedirectResponse("/orders/mine", status_code=302)

# — Send message —
@app.post("/message/{order_id}")
def send_message(
    order_id: int,
    text: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Сделка не найдена")
    msg = Message(order_id=order.id, sender_id=user.id, text=text)
    db.add(msg)
    db.commit()
    return RedirectResponse(f"/trade/{order.id}", status_code=302)

# — My Orders —
@app.get("/orders/mine", response_class=HTMLResponse)
def my_orders(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    orders = db.query(Order).filter(
        (Order.buyer_id == user.id) | (Order.ad.has(user_id=user.id))
    ).all()
    return templates.TemplateResponse("orders.html", {
        "request": request, "orders": orders
    })

# — Profile —
@app.get("/profile", response_class=HTMLResponse)
def profile_view(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return templates.TemplateResponse("profile.html", {
        "request": request, "user": user
    })
