from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from datetime import datetime, timedelta
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory хранилища
ads = []
chats = {}
payments = {}
order_status = {}
blocked_until = {}
cancellations = {}
balances = {}

def get_current_user():
    return "Павел"  # ваша логика аутентификации

def check_block(user: str):
    until = blocked_until.get(user)
    if until and datetime.utcnow() < until:
        raise HTTPException(403, f"Заблокирован до {until.strftime('%Y-%m-%d %H:%M')}")

@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse("/market", 302)

@app.get("/market", response_class=HTMLResponse)
def market(request: Request, user: str = Depends(get_current_user)):
    balances.setdefault(user, 1000.0)
    return templates.TemplateResponse("market.html", {
        "request": request,
        "ads": ads,
        "balances": balances,
        "current_user": user
    })

@app.get("/create", response_class=HTMLResponse)
def create_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create")
def create_ad(
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
    ad_id = uuid4().hex
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
    chats[ad_id] = []
    payments[ad_id] = {}
    order_status[ad_id] = None
    return RedirectResponse("/market", 302)

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade_view(request: Request, ad_id: str, user: str = Depends(get_current_user)):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "messages": chats[ad_id],
        "payments": payments[ad_id],
        "status": order_status[ad_id],
        "balances": balances,
        "current_user": user,
        "blocked_until": blocked_until.get(user),
        "now": datetime.utcnow
    })

@app.post("/trade/{ad_id}/buy")
def trade_buy(ad_id: str, amount: float = Form(...), user: str = Depends(get_current_user)):
    check_block(user)
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    cost = amount * ad["rate"]
    if balances[user] < cost:
        raise HTTPException(400, "Недостаточно средств")
    balances[user] -= cost
    payments[ad_id] = {"user": user, "amount": amount, "cost": cost, "paid": False}
    order_status[ad_id] = "pending"
    return RedirectResponse(f"/trade/{ad_id}", 302)

@app.post("/trade/{ad_id}/pay")
def trade_pay(ad_id: str, user: str = Depends(get_current_user)):
    check_block(user)
    pay = payments.get(ad_id)
    if not pay or pay.get("paid"):
        raise HTTPException(400, "Нельзя оплатить")
    pay["paid"] = True
    order_status[ad_id] = "paid"
    return RedirectResponse(f"/trade/{ad_id}", 302)

@app.post("/trade/{ad_id}/confirm_receipt")
def confirm_receipt(ad_id: str, user: str = Depends(get_current_user)):
    check_block(user)
    if order_status.get(ad_id) != "paid":
        raise HTTPException(400, "Нельзя подтвердить получение")
    order_status[ad_id] = "released"
    seller = payments[ad_id]["user"]
    balances[seller] = balances.get(seller, 0.0) + payments[ad_id]["cost"] * 0.99
    return RedirectResponse(f"/trade/{ad_id}", 302)

@app.post("/trade/{ad_id}/cancel")
def cancel_trade(ad_id: str, user: str = Depends(get_current_user)):
    check_block(user)
    cancellations[user] = cancellations.get(user, 0) + 1
    if cancellations[user] >= 10:
        blocked_until[user] = datetime.utcnow() + timedelta(hours=24)
    order_status[ad_id] = "cancelled"
    return RedirectResponse(f"/trade/{ad_id}", 302)

@app.post("/trade/{ad_id}/dispute")
def dispute_trade(ad_id: str, user: str = Depends(get_current_user)):
    check_block(user)
    order_status[ad_id] = "disputed"
    return RedirectResponse(f"/trade/{ad_id}", 302)

@app.post("/trade/{ad_id}/message")
async def chat_message(
    ad_id: str,
    message: str = Form(""),
    image: UploadFile = File(None),
    user: str = Depends(get_current_user)
):
    check_block(user)
    entry = {"user": user, "text": message}
    if image:
        os.makedirs("static/uploads", exist_ok=True)
        path = f"static/uploads/{uuid4().hex}_{image.filename}"
        with open(path, "wb") as f:
            f.write(await image.read())
        entry["image_url"] = path.replace("static", "/static")
    chats[ad_id].append(entry)
    low = message.lower()
    if "оператор" in low:
        print(f"[УВЕДОМЛЕНИЕ] {user} просит оператора в {ad_id}")
    if any(k in low for k in ["бот","help","чатгпт"]):
        chats[ad_id].append({"user":"Бот","text":f"Привет, {user}! Чем помочь?"})
    return RedirectResponse(f"/trade/{ad_id}", 302)

# ====== Пополнение ======
@app.get("/deposit", response_class=HTMLResponse)
def deposit_form(request: Request, user: str = Depends(get_current_user)):
    balance = balances.get(user, 0.0)
    return templates.TemplateResponse("deposit.html", {
        "request": request,
        "current_user": user,
        "balance": balance
    })

@app.post("/deposit")
def deposit(request: Request, amount: float = Form(...), user: str = Depends(get_current_user)):
    if amount <= 0:
        raise HTTPException(400, "Введите сумму больше нуля")
    balances[user] = balances.get(user, 0.0) + amount
    return RedirectResponse("/market", 302)

# ====== Вывод ======
@app.get("/withdraw", response_class=HTMLResponse)
def withdraw_form(request: Request, user: str = Depends(get_current_user)):
    balance = balances.get(user, 0.0)
    return templates.TemplateResponse("withdraw.html", {
        "request": request,
        "current_user": user,
        "balance": balance
    })

@app.post("/withdraw")
def withdraw(request: Request, amount: float = Form(...), wallet_address: str = Form(...), user: str = Depends(get_current_user)):
    if amount <= 0 or amount > balances.get(user, 0.0):
        raise HTTPException(400, "Неверная сумма")
    if not wallet_address:
        raise HTTPException(400, "Укажите адрес кошелька")
    balances[user] -= amount
    # здесь вы бы инициировали реальный вывод
    return RedirectResponse("/market", 302)
