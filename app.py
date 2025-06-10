from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from typing import List
import uvicorn

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

ads = []
orders = {}
chat_messages = {}

# Главная (Маркет)
@app.get("/", response_class=HTMLResponse)
def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

# Страница создания объявления
@app.get("/create", response_class=HTMLResponse)
def create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create")
def create_ad(title: str = Form(...), amount: float = Form(...), payment_method: str = Form(...)):
    ad = {"id": str(uuid4()), "title": title, "amount": amount, "payment_method": payment_method}
    ads.append(ad)
    return RedirectResponse(url="/", status_code=303)

# Купить -> перейти в сделку
@app.get("/buy/{ad_id}", response_class=HTMLResponse)
def start_trade(request: Request, ad_id: str):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        return HTMLResponse("Объявление не найдено", status_code=404)

    order_id = str(uuid4())
    orders[order_id] = ad
    chat_messages[order_id] = []
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "order_id": order_id,
        "amount": ad["amount"],
        "payment_method": ad["payment_method"],
        "messages": chat_messages[order_id]
    })

# Я оплатил
@app.post("/orders/{order_id}/paid")
def paid(order_id: str):
    return RedirectResponse(url=f"/orders/{order_id}", status_code=303)

# Подтвердить получение
@app.post("/orders/{order_id}/confirm")
def confirm(order_id: str):
    return RedirectResponse(url=f"/orders/{order_id}", status_code=303)

# Открыть спор
@app.post("/orders/{order_id}/dispute")
def dispute(order_id: str):
    return RedirectResponse(url=f"/orders/{order_id}", status_code=303)

# Сообщение в чат
@app.post("/orders/{order_id}/message")
def send_message(order_id: str, text: str = Form(...)):
    chat_messages[order_id].append({"sender": "Вы", "text": text})
    return RedirectResponse(url=f"/orders/{order_id}", status_code=303)

# Страница сделки
@app.get("/orders/{order_id}", response_class=HTMLResponse)
def show_order(request: Request, order_id: str):
    order = orders.get(order_id)
    if not order:
        return HTMLResponse("Сделка не найдена", status_code=404)

    return templates.TemplateResponse("trade.html", {
        "request": request,
        "order_id": order_id,
        "amount": order["amount"],
        "payment_method": order["payment_method"],
        "messages": chat_messages[order_id]
    })

# Локальный запуск (удалить если деплой на Render)
if __name__ == "__main__":
    uvicorn.run("app:app", port=8000, reload=True)
