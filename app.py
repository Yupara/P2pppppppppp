from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4

# Создание FastAPI-приложения
app = FastAPI()

# Подключение папки со статикой и шаблонами
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Временные базы данных (в памяти)
ads = {}
orders = {}
chat = {}

# Главная страница /market
@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    return templates.TemplateResponse("market.html", {
        "request": request,
        "ads": list(ads.values())
    })

# Создание объявления
@app.post("/create-ad")
def create_ad(
    type: str = Form(...),
    amount: float = Form(...),
    currency: str = Form(...),
    payment_method: str = Form(...),
):
    ad_id = str(uuid4())
    ads[ad_id] = {
        "id": ad_id,
        "type": type,
        "amount": amount,
        "currency": currency,
        "payment_method": payment_method
    }
    return RedirectResponse(url="/", status_code=302)

# Страница сделки (trade)
@app.get("/trade/{order_id}", response_class=HTMLResponse)
def trade_page(request: Request, order_id: str):
    ad = ads.get(order_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")

    if order_id not in orders:
        orders[order_id] = {
            "id": order_id,
            "seller": "Продавец",
            "amount": ad["amount"],
            "currency": ad["currency"],
            "payment_method": ad["payment_method"],
            "status": "waiting"
        }
    if order_id not in chat:
        chat[order_id] = []

    return templates.TemplateResponse("trade.html", {
        "request": request,
        "order": orders[order_id],
        "messages": chat[order_id]
    })

# Кнопка "Я оплатил"
@app.post("/orders/{order_id}/paid")
def mark_paid(order_id: str):
    if order_id in orders:
        orders[order_id]["status"] = "paid"
    return RedirectResponse(url=f"/trade/{order_id}", status_code=302)

# Кнопка "Подтвердить получение"
@app.post("/orders/{order_id}/confirm")
def mark_confirm(order_id: str):
    if order_id in orders:
        orders[order_id]["status"] = "confirmed"
    return RedirectResponse(url=f"/trade/{order_id}", status_code=302)

# Кнопка "Открыть спор"
@app.post("/orders/{order_id}/dispute")
def mark_dispute(order_id: str):
    if order_id in orders:
        orders[order_id]["status"] = "dispute"
    return RedirectResponse(url=f"/trade/{order_id}", status_code=302)

# Отправка сообщения в чат
@app.post("/orders/{order_id}/message")
def send_message(order_id: str, message: str = Form(...)):
    if order_id in chat:
        chat[order_id].append({"user": "Вы", "text": message})
    return RedirectResponse(url=f"/trade/{order_id}", status_code=302)
