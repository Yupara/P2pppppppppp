from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI()

# Подключение папки со статикой (CSS и др.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключение шаблонов
templates = Jinja2Templates(directory="templates")

# Простейшие временные модели
class Ad(BaseModel):
    id: str
    type: str  # 'buy' или 'sell'
    amount: float
    price: float
    payment: str
    seller: str

ads_db: List[Ad] = []


# Главная страница
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Страница рынка (объявления)
@app.get("/market", response_class=HTMLResponse)
def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads_db})


# Создание объявления (GET форма)
@app.get("/create", response_class=HTMLResponse)
def create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})


# Создание объявления (POST)
@app.post("/create")
def create_ad(
    type: str = Form(...),
    amount: float = Form(...),
    price: float = Form(...),
    payment: str = Form(...),
    seller: str = Form(...)
):
    ad = Ad(
        id=str(uuid4()),
        type=type,
        amount=amount,
        price=price,
        payment=payment,
        seller=seller
    )
    ads_db.append(ad)
    return RedirectResponse(url="/market", status_code=302)


# Страница сделки (простая заглушка)
@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade(request: Request, ad_id: str):
    ad = next((a for a in ads_db if a.id == ad_id), None)
    if not ad:
        return templates.TemplateResponse("error.html", {"request": request, "msg": "Объявление не найдено"})
    return templates.TemplateResponse("trade.html", {"request": request, "ad": ad})


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
