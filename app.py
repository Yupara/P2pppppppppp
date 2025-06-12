from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException, Depends
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
ads = []             # объявления
chats = {}           # ad_id -> list of messages
payments = {}        # ad_id -> payment info
order_status = {}    # ad_id -> статус сделки
receipts = {}        # ad_id -> bool
cancellations = {}   # user -> count of cancels
blocked_until = {}   # user -> datetime until which blocked
balances = {}        # user -> float balance

# Для упрощения один “текущий” пользователь
def get_current_user():
    return "Павел"

# AUTO-BLOCK CHECK
def check_block(user: str):
    until = blocked_until.get(user)
    if until and datetime.utcnow() < until:
        raise HTTPException(403, f"Заблокирован до {until.isoformat()}")

@app.post("/trade/{ad_id}/cancel")
def cancel_trade(ad_id: str, user: str = Depends(get_current_user)):
    check_block(user)
    # увеличиваем счётчик отмен
    cnt = cancellations.get(user, 0) + 1
    cancellations[user] = cnt
    if cnt >= 10:
        blocked_until[user] = datetime.utcnow() + timedelta(hours=24)
    order_status[ad_id] = "cancelled"
    return RedirectResponse(f"/trade/{ad_id}", 302)

# CHAT WITH BOT
@app.post("/trade/{ad_id}/message")
async def chat_message(
    ad_id: str,
    message: str = Form(None),
    image: UploadFile = File(None),
    user: str = Depends(get_current_user)
):
    check_block(user)
    entry = {"user": user, "text": message or ""}
    if image:
        os.makedirs("static/uploads", exist_ok=True)
        path = f"static/uploads/{uuid4().hex}_{image.filename}"
        with open(path, "wb") as f:
            f.write(await image.read())
        entry["image_url"] = path.replace("static", "/static")
    chats.setdefault(ad_id, []).append(entry)

    # Если в тексте слово "оператор" — уведомляем вас (здесь лог в консоль)
    if message and "оператор" in message.lower():
        print(f"[УВЕДОМЛЕНИЕ] Пользователь {user} попросил оператора в объявлении {ad_id}")

    # Если слово "бот" или "help" — отвечаем ботом
    if message and any(k in message.lower() for k in ["бот", "help", "чатгпт"]):
        bot_reply = f"Привет, {user}! Я бот-помощник. Чем могу помочь?"
        chats[ad_id].append({"user": "Бот", "text": bot_reply})

    return RedirectResponse(f"/trade/{ad_id}", 302)

# При покупке списываем баланс, удерживаем в эскроу
@app.post("/trade/{ad_id}/buy")
def trade_buy(ad_id: str, amount: float = Form(...), user: str = Depends(get_current_user)):
    check_block(user)
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(404, "Ad not found")
    # Проверяем баланс
    bal = balances.get(user, 1000.0)  # начальный баланс 1000
    cost = amount * ad["rate"]
    if bal < cost:
        raise HTTPException(400, "Недостаточно средств")
    # списываем и удерживаем
    balances[user] = bal - cost
    payments[ad_id] = {"user": user, "amount": amount, "cost": cost, "paid": False}
    order_status[ad_id] = "pending"
    return RedirectResponse(f"/trade/{ad_id}", 302)

# при успешном завершении (release), переводим средства продавцу
@app.post("/trade/{ad_id}/confirm_receipt")
def confirm_receipt(ad_id: str, user: str = Depends(get_current_user)):
    check_block(user)
    if order_status.get(ad_id) != "paid":
        raise HTTPException(400, "Нельзя подтвердить")
    order_status[ad_id] = "released"
    # Добавляем продавцу
    pay = payments[ad_id]
    seller = next(a for a in ads if a["id"] == ad_id)["owner"]
    balances[seller] = balances.get(seller, 0.0) + pay["cost"] * (1 - 0.01)  # комиссия 1%
    receipts[ad_id] = True
    return RedirectResponse(f"/trade/{ad_id}", 302)
