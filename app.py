from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from datetime import datetime, timedelta

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

ads = []
chats = {}  # chat history

# Инициализация тестового объявления
ads.append({
    "id": "ad-1",
    "action": "buy",
    "crypto": "USDT",
    "fiat": "RUB",
    "rate": 1.0,
    "min_amount": 1,
    "max_amount": 10000,
    "payment_method": "Сбербанк, Тинькофф",
    "comment": "Без дополнительных условий",
    "user": "Павел",
    "rating": 99,
    "orders": 55
})
chats["ad-1"] = []

@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse("/market", status_code=302)

@app.get("/market", response_class=HTMLResponse)
def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade_get(request: Request, ad_id: str):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    # чат
    chat = chats.get(ad_id, [])
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "chat": chat,
        "summary": None
    })

@app.post("/trade/{ad_id}/buy", response_class=HTMLResponse)
def trade_buy(request: Request, ad_id: str, usdt_amount: float = Form(...)):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    # расчёты
    rate = ad["rate"]
    total_rub = usdt_amount * rate
    commission = total_rub * 0.005  # 0.5%
    timestamp = datetime.utcnow().strftime("%Y.%m.%d %H:%M")
    summary = {
        "usdt_amount": usdt_amount,
        "rate": rate,
        "total_rub": total_rub,
        "commission": commission,
        "timestamp": timestamp,
        "buyer": "Павел"
    }
    chat = chats.get(ad_id, [])
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "chat": chat,
        "summary": summary
    })

@app.post("/trade/{ad_id}/message")
def trade_message(ad_id: str, message: str = Form(...)):
    if ad_id in chats:
        chats[ad_id].append({"user": "Вы", "text": message})
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)
