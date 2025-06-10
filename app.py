from fastapi import FastAPI, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uvicorn
import os

from database import Base, engine, SessionLocal
from models import User, Ad

app = FastAPI()

# Статика и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Зависимость подключения к БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 👉 Добавление тестового пользователя и объявления
def create_test_data():
    db = SessionLocal()
    existing_user = db.query(User).filter_by(username="seller123").first()
    if existing_user:
        db.close()
        return
    seller = User(username="seller123", hashed_password="123456")
    db.add(seller)
    db.commit()
    db.refresh(seller)
    ad = Ad(
        user_id=seller.id,
        ad_type="sell",
        amount=100,
        price=1.0,
        currency="USDT",
        payment_method="Bank",
        description="Test USDT sale"
    )
    db.add(ad)
    db.commit()
    db.close()

# ⏩ Вызов функции при старте
create_test_data()

# 🔹 Главная
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 🔹 Маркет
@app.get("/market", response_class=HTMLResponse)
def market(request: Request, db: Session = Depends(get_db)):
    ads = db.query(Ad).all()
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

# 🔹 Купить
@app.post("/buy/{ad_id}")
def buy(ad_id: int, db: Session = Depends(get_db)):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        return {"error": "Ad not found"}
    return RedirectResponse(url="/market", status_code=302)

# 🔹 Запуск сервера
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
