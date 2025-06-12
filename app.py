from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException, Depends
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

# Хранилища в памяти
ads = []              # объявления
chats = {}            # ad_id -> сообщения
payments = {}         # ad_id -> {amount, paid,...}
order_status = {}     # ad_id -> статус
blocked_until = {}    # user -> datetime блокировки
balances = {}         # user -> баланс

# Фейковая аутентификация
def get_current_user():
    return "Павел"

# Главная → рынок
@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse("/market", 302)

# Рынок
@app.get("/market", response_class=HTMLResponse)
def market(request: Request, user: str = Depends(get_current_user)):
    balances.setdefault(user, 1000.0)
    return templates.TemplateResponse("market.html", {
        "request": request,
        "ads": ads,
        "balances": balances,
        "current_user": user
    })

# Форма создания объявления
@app.get("/create", response_class=HTMLResponse)
def create_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

# Обработка создания объявления
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
    chats[ad_id] = []
    payments[ad_id] = {}
    order_status[ad_id] = None
    return RedirectResponse("/market", 302)

# Страница сделки
@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade_view(request: Request, ad_id: str, user: str = Depends(get_current_user)):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    remaining = 15 * 60
    balances.setdefault(user, 1000.0)
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "remaining": remaining,
        "chats": chats[ad_id],
        "payments": payments[ad_id],
        "status": order_status[ad_id],
        "balances": balances,
        "current_user": user,
        "blocked_until": blocked_until.get(user),
        "now": datetime.utcnow
    })

# Купить (создать ордер)
@app.post("/trade/{ad_id}/buy")
def trade_buy(ad_id: str, amount: float = Form(...), user: str = Depends(get_current_user)):
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

# Оплатил
@app.post("/trade/{ad_id}/pay")
def trade_pay(ad_id: str, user: str = Depends(get_current_user)):
    payments[ad_id]["paid"] = True
    order_status[ad_id] = "paid"
    return RedirectResponse(f"/trade/{ad_id}", 302)

# Подтвердить получение
@app.post("/trade/{ad_id}/confirm_receipt")
def confirm_receipt(ad_id: str, user: str = Depends(get_current_user)):
    if order_status[ad_id] != "paid":
        raise HTTPException(400, "Нельзя подтвердить")
    order_status[ad_id] = "released"
    # перевод продавцу (с учётом 1% комиссии)
    seller = payments[ad_id]["user"]
    balances[seller] = balances.get(seller, 0) + payments[ad_id]["cost"] * 0.99
    return RedirectResponse(f"/trade/{ad_id}", 302)

# Отмена
@app.post("/trade/{ad_id}/cancel")
def cancel(ad_id: str, user: str = Depends(get_current_user)):
    order_status[ad_id] = "cancelled"
    return RedirectResponse(f"/trade/{ad_id}", 302)

# Спор
@app.post("/trade/{ad_id}/dispute")
def dispute(ad_id: str, user: str = Depends(get_current_user)):
    order_status[ad_id] = "disputed"
    return RedirectResponse(f"/trade/{ad_id}", 302)

# Чат + изображения
@app.post("/trade/{ad_id}/message")
async def chat_message(ad_id: str, message: str = Form(""), image: UploadFile = File(None), user: str = Depends(get_current_user)):
    entry = {"user": user, "text": message}
    if image:
        os.makedirs("static/uploads", exist_ok=True)
        path = f"static/uploads/{uuid4().hex}_{image.filename}"
        with open(path, "wb") as f:
            f.write(await image.read())
        entry["image_url"] = path.replace("static", "/static")
    chats[ad_id].append(entry)
    return RedirectResponse(f"/trade/{ad_id}", 302)
