# app.py

import os
from datetime import datetime
from fastapi import (
    FastAPI, Request, Form, Depends,
    HTTPException, status
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from sqlalchemy import (
    create_engine, Column, Integer,
    String, Float, ForeignKey, DateTime, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# --- БАЗА ДАННЫХ ---
DATABASE_URL = "sqlite:///./p2p.db"
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- МОДЕЛИ ---
class User(Base):
    __tablename__ = "users"
    id       = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    # отношение к объявлениям и сделкам
    ads      = relationship("Ad", back_populates="user")
    trades   = relationship("Trade", back_populates="buyer")
    # для блокировки
    cancel_count = Column(Integer, default=0)
    is_blocked   = Column(Integer, default=0)  # 0/1

class Ad(Base):
    __tablename__ = "ads"
    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"))
    type            = Column(String, nullable=False)  # buy/sell
    crypto          = Column(String, nullable=False)
    fiat            = Column(String, nullable=False)
    amount          = Column(Float, nullable=False)
    price           = Column(Float, nullable=False)
    min_limit       = Column(Float, nullable=False)
    max_limit       = Column(Float, nullable=False)
    payment_methods = Column(String, nullable=False)
    user            = relationship("User", back_populates="ads")
    trades          = relationship("Trade", back_populates="ad")

class Trade(Base):
    __tablename__ = "trades"
    id         = Column(Integer, primary_key=True, index=True)
    buyer_id   = Column(Integer, ForeignKey("users.id"))
    ad_id      = Column(Integer, ForeignKey("ads.id"))
    amount     = Column(Float, nullable=False)
    status     = Column(String, default="pending")  # pending, paid, confirmed, disputed
    created_at = Column(DateTime, default=datetime.utcnow)
    buyer      = relationship("User", back_populates="trades")
    ad         = relationship("Ad", back_populates="trades")

class Message(Base):
    __tablename__ = "messages"
    id        = Column(Integer, primary_key=True, index=True)
    trade_id  = Column(Integer, ForeignKey("trades.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    text      = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sender    = relationship("User")
    trade     = relationship("Trade")

# создаём таблицы
Base.metadata.create_all(bind=engine)

# --- FASTAPI APP ---
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY","secret123"))
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- УТИЛИТА ДЛЯ АВТОРИЗАЦИИ ---
def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(status_code=401, detail="Не авторизован")
    user = db.query(User).get(uid)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="Аккаунт заблокирован")
    return user

# --- МАРШРУТЫ ---

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/market")

@app.get("/market", response_class=HTMLResponse)
def market(request: Request, db: Session = Depends(get_db)):
    ads = db.query(Ad).all()
    html = ["<h1>Рынок P2P</h1><ul>"]
    for ad in ads:
        html.append(
            f"<li>{ad.crypto}/{ad.fiat} @ {ad.price} "
            f"[{ad.min_limit}-{ad.max_limit}] "
            f"<a href='/trade/create/{ad.id}'>Купить</a></li>"
        )
    html.append("</ul><p><a href='/login'>Войти</a> | <a href='/register'>Регистрация</a></p>")
    return HTMLResponse("\n".join(html))

@app.get("/register", response_class=HTMLResponse)
def register_form():
    return HTMLResponse("""
        <h1>Регистрация</h1>
        <form action="/register" method="post">
          <input name="username" placeholder="Логин" required><br>
          <input name="password" type="password" placeholder="Пароль" required><br>
          <button>Зарегистрироваться</button>
        </form>
    """)

@app.post("/register")
def register(request: Request,
             username: str = Form(...),
             password: str = Form(...),
             db: Session = Depends(get_db)):
    if db.query(User).filter_by(username=username).first():
        return HTMLResponse("Логин уже занят", status_code=400)
    u = User(username=username, password=password)
    db.add(u); db.commit(); db.refresh(u)
    request.session["user_id"] = u.id
    return RedirectResponse("/market", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_form():
    return HTMLResponse("""
        <h1>Вход</h1>
        <form action="/login" method="post">
          <input name="username" placeholder="Логин" required><br>
          <input name="password" type="password" placeholder="Пароль" required><br>
          <button>Войти</button>
        </form>
    """)

@app.post("/login")
def login(request: Request,
          username: str = Form(...),
          password: str = Form(...),
          db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=username, password=password).first()
    if not user:
        return HTMLResponse("Неверные данные", status_code=401)
    request.session["user_id"] = user.id
    return RedirectResponse("/market", status_code=302)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/market")

@app.get("/create_ad", response_class=HTMLResponse)
def create_ad_form():
    return HTMLResponse("""
        <h1>Новое объявление</h1>
        <form action="/create_ad" method="post">
          <input name="type" placeholder="buy/sell" required><br>
          <input name="crypto" placeholder="USDT" required><br>
          <input name="fiat" placeholder="RUB" required><br>
          <input name="amount" type="number" step="0.01" placeholder="Сумма" required><br>
          <input name="price" type="number" step="0.01" placeholder="Цена" required><br>
          <input name="min_limit" type="number" step="0.01" placeholder="Мин лимит" required><br>
          <input name="max_limit" type="number" step="0.01" placeholder="Макс лимит" required><br>
          <input name="payment_methods" placeholder="Способы оплаты" required><br>
          <button>Опубликовать</button>
        </form>
    """)

@app.post("/create_ad")
def create_ad(request: Request,
              type: str = Form(...),
              crypto: str = Form(...),
              fiat: str = Form(...),
              amount: float = Form(...),
              price: float = Form(...),
              min_limit: float = Form(...),
              max_limit: float = Form(...),
              payment_methods: str = Form(...),
              db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    ad = Ad(
        user_id=user.id, type=type,
        crypto=crypto, fiat=fiat,
        amount=amount, price=price,
        min_limit=min_limit, max_limit=max_limit,
        payment_methods=payment_methods
    )
    db.add(ad); db.commit()
    return RedirectResponse("/market", status_code=302)

@app.get("/trade/create/{ad_id}")
def create_trade(ad_id: int,
                 db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    ad = db.query(Ad).get(ad_id)
    if not ad or ad.user_id == user.id:
        raise HTTPException(400, "Невозможно купить")
    trade = Trade(buyer_id=user.id, ad_id=ad.id, amount=ad.amount)
    db.add(trade); db.commit(); db.refresh(trade)
    return RedirectResponse(f"/trade/{trade.id}", status_code=302)

@app.get("/trade/{trade_id}", response_class=HTMLResponse)
def view_trade(trade_id: int,
               request: Request,
               db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    trade = db.query(Trade).get(trade_id)
    if not trade or (trade.buyer_id != user.id and trade.ad.user_id != user.id):
        raise HTTPException(404, "Сделка не найдена")
    # кнопки действий и чат
    html = [f"<h1>Сделка #{trade.id}</h1>",
            f"<p>Сумма: {trade.amount} {trade.ad.crypto}</p>",
            f"<p>Статус: {trade.status}</p>"]
    if trade.status == "pending" and trade.buyer_id == user.id:
        html.append(f"<form action='/trade/{trade.id}/paid' method='post'><button>Я оплатил</button></form>")
    if trade.status == "paid" and trade.ad.user_id == user.id:
        html.append(f"<form action='/trade/{trade.id}/confirm' method='post'><button>Подтвердить получение</button></form>")
    html.append(f"<form action='/trade/{trade.id}/dispute' method='post'><button>Открыть спор</button></form>")
    # чат
    msgs = db.query(Message).filter(Message.trade_id == trade.id).order_by(Message.timestamp).all()
    html.append("<h3>Чат</h3><div>")
    for m in msgs:
        html.append(f"<p><strong>{m.sender.username}:</strong> {m.text}</p>")
    html.append("</div>")
    html.append(f"""
        <form action="/trade/{trade.id}/message" method="post">
          <input name="text" placeholder="Сообщение" required>
          <button>Отправить</button>
        </form>
    """)
    return HTMLResponse("\n".join(html))

@app.post("/trade/{trade_id}/paid")
def mark_paid(trade_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = db.query(Trade).get(trade_id)
    if not t or t.buyer_id != user.id: raise HTTPException(403)
    t.status = "paid"; db.commit()
    return RedirectResponse(f"/trade/{trade_id}", status_code=302)

@app.post("/trade/{trade_id}/confirm")
def mark_confirm(trade_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = db.query(Trade).get(trade_id)
    if not t or t.ad.user_id != user.id: raise HTTPException(403)
    t.status = "confirmed"; db.commit()
    return RedirectResponse(f"/trade/{trade_id}", status_code=302)

@app.post("/trade/{trade_id}/dispute")
def mark_dispute(trade_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = db.query(Trade).get(trade_id)
    if not t or (user.id not in (t.buyer_id, t.ad.user_id)): raise HTTPException(403)
    t.status = "disputed"; db.commit()
    return RedirectResponse(f"/trade/{trade_id}", status_code=302)

@app.post("/trade/{trade_id}/message")
def send_message(trade_id: int,
                 request: Request,
                 text: str = Form(...),
                 db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    t = db.query(Trade).get(trade_id)
    if not t or (user.id not in (t.buyer_id, t.ad.user_id)): raise HTTPException(403)
    m = Message(trade_id=trade_id, sender_id=user.id, text=text)
    db.add(m); db.commit()
    return RedirectResponse(f"/trade/{trade_id}", status_code=302)
