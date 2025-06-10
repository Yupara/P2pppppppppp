from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from uuid import uuid4
import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Временное хранилище (вместо базы данных)
ads = []
trades = []
chat_messages = {}

# Модель объявления
class Ad(BaseModel):
    id: str
    type: str  # buy / sell
    amount: float
    price: float
    payment_method: str

# Главная страница с объявлениями
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

# Создание объявления
@app.post("/create_ad")
def create_ad(
    type: str = Form(...),
    amount: float = Form(...),
    price: float = Form(...),
    payment_method: str = Form(...)
):
    ad_id = str(uuid4())
    ad = Ad(id=ad_id, type=type, amount=amount, price=price, payment_method=payment_method)
    ads.append(ad)
    return RedirectResponse("/", status_code=302)

# Покупка (создание сделки)
@app.get("/buy/{ad_id}", response_class=HTMLResponse)
def buy_ad(ad_id: str, request: Request):
    ad = next((a for a in ads if a.id == ad_id), None)
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    
    trade_id = str(uuid4())
    trade = {
        "id": trade_id,
        "ad": ad,
        "start_time": datetime.datetime.utcnow(),
        "status": "active",
        "messages": []
    }
    trades.append(trade)
    chat_messages[trade_id] = []

    return templates.TemplateResponse("trade.html", {"request": request, "trade": trade})

# Отправка сообщений в чате
@app.post("/chat/{trade_id}")
def chat(trade_id: str, message: str = Form(...)):
    if trade_id not in chat_messages:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    chat_messages[trade_id].append(message)
    return RedirectResponse(f"/buy/{trade_id}", status_code=302)
