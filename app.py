from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Float, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import enum
import os

# === Настройка базы данных ===
DATABASE_URL = "sqlite:///./ads.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# === Типы сделок ===
class AdType(str, enum.Enum):
    buy = "buy"
    sell = "sell"

# === Модель объявления ===
class Ad(Base):
    __tablename__ = "ads"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(AdType), nullable=False)
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)

# === Создание таблицы ===
Base.metadata.create_all(bind=engine)

# === Инициализация FastAPI ===
app = FastAPI()

# === Подключение шаблонов и статики ===
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# === Зависимость для сессии БД ===
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === Главная страница: список объявлений ===
@app.get("/", response_class=HTMLResponse)
def read_index(request: Request, db: Session = Depends(get_db)):
    ads = db.query(Ad).all()
    return templates.TemplateResponse("index.html", {"request": request, "ads": ads})

# === Страница создания объявления ===
@app.get("/create", response_class=HTMLResponse)
def create_ad_form(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})

# === Обработка создания объявления ===
@app.post("/create")
def create_ad(
    type: AdType = Form(...),
    price: float = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db)
):
    ad = Ad(type=type, price=price, amount=amount)
    db.add(ad)
    db.commit()
    db.refresh(ad)
    return RedirectResponse("/", status_code=302)

# === Просмотр отдельного объявления ===
@app.get("/order/{ad_id}", response_class=HTMLResponse)
def view_order(ad_id: int, request: Request, db: Session = Depends(get_db)):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return templates.TemplateResponse("order.html", {"request": request, "ad": ad})
