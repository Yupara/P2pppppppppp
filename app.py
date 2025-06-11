from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Данные в памяти
ads = {}
orders = {}
chat = {}

@app.post("/create-ad")
def create_ad(type: str = Form(...), amount: float = Form(...), currency: str = Form(...), payment_method: str = Form(...)):
    ad_id = str(uuid4())
    ads[ad_id] = {
        "id": ad_id, "type": type, "amount": amount,
        "currency": currency, "payment_method": payment_method
    }
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

@app.get("/trade/{order_id}", response_class=HTMLResponse)
def open_trade(request: Request, order_id: str):
    ad = ads.get(order_id)
    if not ad:
        raise HTTPException(404, "Сделка не найдена")
    # Инициализировать order и чат, если первый визит
    orders.setdefault(order_id, {"id": order_id, **ad, "seller": "Продавец", "status": "waiting"})
    chat.setdefault(order_id, [])
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "order": orders[order_id],
        "messages": chat[order_id]
    })

@app.post("/orders/{order_id}/paid")
def paid(order_id: str):
    if order_id in orders:
        orders[order_id]["status"] = "paid"
    return RedirectResponse(f"/trade/{order_id}", status_code=302)

@app.post("/orders/{order_id}/confirm")
def confirm(order_id: str):
    if order_id in orders:
        orders[order_id]["status"] = "confirmed"
    return RedirectResponse(f"/trade/{order_id}", status_code=302)

@app.post("/orders/{order_id}/dispute")
def dispute(order_id: str):
    if order_id in orders:
        orders[order_id]["status"] = "dispute"
    return RedirectResponse(f"/trade/{order_id}", status_code=302)

@app.post("/orders/{order_id}/message")
def send_message(order_id: str, message: str = Form(...)):
    if order_id in chat:
        chat[order_id].append({"user": "Вы", "text": message})
    return RedirectResponse(f"/trade/{order_id}", status_code=302)
