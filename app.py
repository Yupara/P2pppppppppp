from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from datetime import datetime, timedelta

app = FastAPI()

# Подключаем статику и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory хранилище
ads = []
chats = {}
payments = {}
receipts = {}

# Главная → рынок
@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse("/market", status_code=302)

# Список объявлений
@app.get("/market", response_class=HTMLResponse)
def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

# Форма создания объявления
@app.get("/create", response_class=HTMLResponse)
def create_get(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

# Обработка создания объявления
@app.post("/create")
def create_post(
    request: Request,
    action: str = Form(...),
    crypto: str = Form(...),
    fiat: str = Form(...),
    rate: float = Form(...),
    min_amount: float = Form(...),
    max_amount: float = Form(...),
    payment_method: str = Form(...),
    comment: str = Form("")
):
    ad_id = str(uuid4())
    ad = {
        "id": ad_id,
        "action": action,
        "crypto": crypto,
        "fiat": fiat,
        "rate": rate,
        "min_amount": min_amount,
        "max_amount": max_amount,
        "payment_method": payment_method,
        "comment": comment,
        "user": "Павел",
        "rating": 99,
        "orders": 55
    }
    ads.append(ad)
    chats[ad_id] = []
    return RedirectResponse("/market", status_code=302)

# Страница сделки
@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade_get(request: Request, ad_id: str):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    # Таймер 15 минут
    end_time = datetime.utcnow() + timedelta(minutes=15)
    remaining = int((end_time - datetime.utcnow()).total_seconds())
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "remaining": remaining,
        "messages": chats.get(ad_id, []),
        "payments": payments,
        "receipts": receipts
    })

# Чат
@app.post("/trade/{ad_id}/message")
def trade_message(ad_id: str, message: str = Form(...)):
    if ad_id in chats:
        chats[ad_id].append({"user": "Вы", "text": message})
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

# Покупка USDT
@app.post("/trade/{ad_id}/buy")
def trade_buy(ad_id: str, usdt_amount: float = Form(...)):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    # Рассчёт итогов
    total_rub = usdt_amount * ad["rate"]
    commission = total_rub * 0.005
    timestamp = datetime.utcnow().strftime("%Y.%m.%d %H:%M")
    payments[ad_id] = {
        "usdt_amount": usdt_amount,
        "total_rub": total_rub,
        "commission": commission,
        "timestamp": timestamp
    }
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

# Ввод данных карты
@app.post("/trade/{ad_id}/pay")
def trade_pay(
    ad_id: str,
    card_number: str = Form(...),
    exp_date: str = Form(...),
    cvv: str = Form(...)
):
    payments.setdefault(ad_id, {})["paid"] = True
    payments[ad_id].update({"card": card_number, "exp": exp_date, "cvv": cvv})
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

# Подтверждение получения
@app.post("/trade/{ad_id}/confirm_receipt")
def trade_confirm_receipt(ad_id: str):
    if payments.get(ad_id, {}).get("paid"):
        receipts[ad_id] = True
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)
