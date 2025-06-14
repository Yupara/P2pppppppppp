# app.py

from fastapi import (
    FastAPI, Request, Form, Depends,
    HTTPException, status
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from sqlalchemy import (
    create_engine, Column, Integer, String,
    Float, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

import os

# --- ПОДКЛЮЧЕНИЕ БАЗЫ ---
DATABASE_URL = "sqlite:///./p2p.db"
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)
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
    # relation
    ads      = relationship("Ad", back_populates="user")

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

# создаём таблицы
Base.metadata.create_all(bind=engine)

# --- ИНИЦИАЛИЗАЦИЯ APP ---
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "very-secret"))
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Не авторизован")
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user

# --- МАРШРУТЫ ---

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/market")

@app.get("/market", response_class=HTMLResponse)
def market(request: Request, db: Session = Depends(get_db)):
    ads = db.query(Ad).all()
    # Простой HTML-рендеринг:
    html = ["<h1>Рынок P2P</h1><ul>"]
    for ad in ads:
        html.append(
            f"<li>{ad.crypto}/{ad.fiat} @ {ad.price} — "
            f"лимит {ad.min_limit}-{ad.max_limit} — "
            f"<a href='/login'>Купить</a></li>"
        )
    html.append("</ul>")
    html.append(
        "<p><a href='/login'>Войти</a> | <a href='/register'>Регистрация</a></p>"
    )
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
        return HTMLResponse("Логин занят", status_code=400)
    user = User(username=username, password=password)
    db.add(user); db.commit()
    request.session["user_id"] = user.id
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
def create_ad_form(request: Request):
    return HTMLResponse("""
        <h1>Создать объявление</h1>
        <form action="/create_ad" method="post">
          <input name="type" placeholder="buy/sell" required><br>
          <input name="crypto" placeholder="USDT, BTC..." required><br>
          <input name="fiat" placeholder="USD, RUB..." required><br>
          <input name="amount" type="number" step="0.01" placeholder="Сумма" required><br>
          <input name="price" type="number" step="0.01" placeholder="Цена" required><br>
          <input name="min_limit" type="number" step="0.01" placeholder="Мин лимит" required><br>
          <input name="max_limit" type="number" step="0.01" placeholder="Макс лимит" required><br>
          <input name="payment_methods" placeholder="Способы оплаты" required><br>
          <button>Опубликовать</button>
        </form>
    """)

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
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    ad = Ad(
        user_id=user.id,
        type=type,
        crypto=crypto,
        fiat=fiat,
        amount=amount,
        price=price,
        min_limit=min_limit,
        max_limit=max_limit,
        payment_methods=payment_methods
    )
    db.add(ad); db.commit()
    return RedirectResponse("/market", status_code=302)
