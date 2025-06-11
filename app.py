from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from typing import List, Dict
from datetime import datetime, timedelta

app = FastAPI()

# Подключаем статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory хранилище объявлений
ads: List[Dict] = []

# Главная: перенаправляем сразу на рынок
@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse(url="/market", status_code=302)

# Рынок: список объявлений
@app.get("/market", response_class=HTMLResponse)
def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

# Форма создания объявления
@app.get("/create", response_class=HTMLResponse)
def create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

# Обработка формы создания объявления
@app.post("/create")
def create_ad(
    request: Request,
    type: str = Form(...),
    crypto: str = Form(...),
    fiat: str = Form(...),
    rate: float = Form(...),
    amount: float = Form(...),
    payment_method: str = Form(...),
):
    ad = {
        "id": str(uuid4()),
        "type": type,
        "crypto": crypto,
        "fiat": fiat,
        "rate": rate,
        "amount": amount,
        "payment_method": payment_method,
        "created": datetime.utcnow().isoformat()
    }
    ads.append(ad)
    return RedirectResponse(url="/market", status_code=302)

# Сделка: просмотр объявления и создание чата
@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade(request: Request, ad_id: str):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    # вставляем таймер на 15 минут
    end_time = (datetime.utcnow() + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S")
    # чат в памяти
    if "chat" not in ad:
        ad["chat"] = []
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "end_time": end_time
    })

# Отправка сообщения в чат
@app.post("/trade/{ad_id}/message")
def send_message(ad_id: str, message: str = Form(...)):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    ad["chat"].append({"user": "You", "text": message})
    return RedirectResponse(url=f"/trade/{ad_id}", status_code=302)
