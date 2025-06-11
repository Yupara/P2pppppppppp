from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from datetime import datetime, timedelta

app = FastAPI()

# Статика и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory хранилище объявлений и чатов
ads = []
chats = {}
payments = {}
receipts = {}

@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse("/market", status_code=302)

@app.get("/market", response_class=HTMLResponse)
def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

@app.get("/create", response_class=HTMLResponse)
def create_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create")
def create_ad(
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

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade_get(request: Request, ad_id: str):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
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

@app.post("/trade/{ad_id}/message")
def trade_message(ad_id: str, message: str = Form(...)):
    if ad_id in chats:
        chats[ad_id].append({"user": "Вы", "text": message})
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/buy")
def trade_buy(ad_id: str, usdt_amount: float = Form(...)):
    # сохраняем сумму покупки, расчет комиссии и времени заказа
    # но для простоты сразу редиректим обратно
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/pay")
def trade_pay(
    ad_id: str,
    card_number: str = Form(...),
    exp_date: str = Form(...),
    cvv: str = Form(...)
):
    payments[ad_id] = {
        "card": card_number,
        "exp": exp_date,
        "cvv": cvv,
        "paid": True
    }
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/confirm_receipt")
def trade_confirm_receipt(ad_id: str):
    if payments.get(ad_id, {}).get("paid"):
        receipts[ad_id] = True
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)
