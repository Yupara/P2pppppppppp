from fastapi import (
    FastAPI, Request, Form, UploadFile, File,
    Depends, HTTPException, status
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
from uuid import uuid4
from datetime import datetime, timedelta
import os, secrets

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="ВАШ_СЕКРЕТ_ДЛЯ_СЕССИЙ")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ——— Auth helpers ———
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBasic()

def hash_pw(pw: str) -> str:
    return pwd_ctx.hash(pw)

def verify_pw(pw: str, hashed: str) -> bool:
    return pwd_ctx.verify(pw, hashed)

# ——— In-memory storage ———
users = {}       # username -> {email, hashed_password}
ads = []         # list of ads
chats = {}       # ad_id -> list of messages
payments = {}    # ad_id -> payment info
order_status = {}# ad_id -> status
blocked_until = {}   # username -> datetime
cancellations = {}   # username -> count
balances = {}        # username -> float

# ——— Authentication ———
def get_current_user(request: Request) -> str:
    user = request.session.get("user")
    if not user or user not in users:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Не авторизован")
    return user

# ——— Admin BasicAuth ———
ADMIN_USER = "admin"
ADMIN_PASS = "МойСуперПароль123"
def get_admin(credentials: HTTPBasicCredentials = Depends(security)):
    if not (secrets.compare_digest(credentials.username, ADMIN_USER)
            and secrets.compare_digest(credentials.password, ADMIN_PASS)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
            "Неверные учётные данные",
            headers={"WWW-Authenticate":"Basic"})
    return credentials.username

def check_block(user: str):
    until = blocked_until.get(user)
    if until and datetime.utcnow() < until:
        raise HTTPException(403, f"Заблокирован до {until}")

# ——— Routes ———

# Registration
@app.get("/register", response_class=HTMLResponse)
def reg_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@app.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...)
):
    if username in users:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Пользователь уже существует"})
    if password != password2:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Пароли не совпадают"})
    users[username] = {"email": email, "hashed_password": hash_pw(password)}
    request.session["user"] = username
    balances.setdefault(username, 1000.0)
    return RedirectResponse("/market", 302)

# Login
@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    u = users.get(username)
    if not u or not verify_pw(password, u["hashed_password"]):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин или пароль"})
    request.session["user"] = username
    balances.setdefault(username, 1000.0)
    return RedirectResponse("/market", 302)

# Logout
@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", 302)

# Home → Market
@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse("/market", 302)

# Market
@app.get("/market", response_class=HTMLResponse)
def market(request: Request, user: str = Depends(get_current_user)):
    return templates.TemplateResponse("market.html", {
        "request": request,
        "ads": ads,
        "balances": balances,
        "current_user": user
    })

# Create Ad
@app.get("/create", response_class=HTMLResponse)
def create_form(request: Request, user: str = Depends(get_current_user)):
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
    card_number: str = Form(...),
    user: str = Depends(get_current_user)
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

# Trade page
@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade_page(request: Request, ad_id: str, user: str = Depends(get_current_user)):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "messages": chats.get(ad_id, []),
        "status": order_status.get(ad_id),
        "balances": balances,
        "current_user": user,
        "blocked_until": blocked_until.get(user),
        "remaining": 15 * 60,
        "now": datetime.utcnow
    })

# Buy
@app.post("/trade/{ad_id}/buy")
def buy(ad_id: str, amount: float = Form(...), user: str = Depends(get_current_user)):
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

# Pay
@app.post("/trade/{ad_id}/pay")
def pay(ad_id: str, user: str = Depends(get_current_user)):
    check_block(user)
    p = payments.get(ad_id)
    if not p or p["paid"]:
        raise HTTPException(400, "Нельзя оплатить")
    p["paid"] = True
    order_status[ad_id] = "paid"
    return RedirectResponse(f"/trade/{ad_id}", 302)

# Confirm receipt
@app.post("/trade/{ad_id}/confirm")
def confirm(ad_id: str, user: str = Depends(get_current_user)):
    check_block(user)
    if order_status.get(ad_id) != "paid":
        raise HTTPException(400, "Нельзя подтвердить получение")
    order_status[ad_id] = "released"
    seller = payments[ad_id]["user"]
    balances[seller] = balances.get(seller, 0.0) + payments[ad_id]["cost"] * 0.99
    return RedirectResponse(f"/trade/{ad_id}", 302)

# Cancel
@app.post("/trade/{ad_id}/cancel")
def cancel(ad_id: str, user: str = Depends(get_current_user)):
    check_block(user)
    cancellations[user] = cancellations.get(user, 0) + 1
    if cancellations[user] >= 10:
        blocked_until[user] = datetime.utcnow() + timedelta(hours=24)
    order_status[ad_id] = "cancelled"
    return RedirectResponse(f"/trade/{ad_id}", 302)

# Dispute
@app.post("/trade/{ad_id}/dispute")
def dispute(ad_id: str, user: str = Depends(get_current_user)):
    check_block(user)
    order_status[ad_id] = "disputed"
    return RedirectResponse(f"/trade/{ad_id}", 302)

# Chat
@app.post("/trade/{ad_id}/message")
async def message(
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
        print(f"Уведомление: {user} запросил оператора")
    if any(k in low for k in ["бот", "help", "чатгпт"]):
        chats[ad_id].append({"user": "Бот", "text": f"Привет, {user}! Чем помочь?"})
    return RedirectResponse(f"/trade/{ad_id}", 302)

# Deposit
@app.get("/deposit", response_class=HTMLResponse)
def dep_form(request: Request, user: str = Depends(get_current_user)):
    bal = balances.get(user, 0.0)
    return templates.TemplateResponse("deposit.html", {"request": request, "balance": bal})

@app.post("/deposit")
def deposit(amount: float = Form(...), user: str = Depends(get_current_user)):
    if amount <= 0:
        raise HTTPException(400, "Неверная сумма")
    balances[user] = balances.get(user, 0.0) + amount
    return RedirectResponse("/market", 302)

# Withdraw
@app.get("/withdraw", response_class=HTMLResponse)
def w_form(request: Request, user: str = Depends(get_current_user)):
    bal = balances.get(user, 0.0)
    return templates.TemplateResponse("withdraw.html", {"request": request, "balance": bal})

@app.post("/withdraw")
def withdraw(amount: float = Form(...), wallet_address: str = Form(...), user: str = Depends(get_current_user)):
    if amount <= 0 or amount > balances.get(user, 0.0):
        raise HTTPException(400, "Неверная сумма")
    if not wallet_address:
        raise HTTPException(400, "Укажите адрес кошелька")
    balances[user] -= amount
    return RedirectResponse("/market", 302)

# Profile
@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request, user: str = Depends(get_current_user)):
    my_ads = [ad for ad in ads if ad["owner"] == user]
    my_trades = [
        {"id": aid, "status": order_status[aid], **payments.get(aid, {})}
        for aid in payments if payments[aid].get("user") == user
    ]
    comp = sum(1 for s in order_status.values() if s == "released")
    canc = sum(1 for s in order_status.values() if s == "cancelled")
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "current_user": user,
        "balance": balances.get(user, 0.0),
        "rating": my_ads[0]["rating"] if my_ads else 0,
        "completed": comp,
        "cancelled": canc,
        "my_ads": my_ads,
        "my_trades": my_trades
    })

# Admin
@app.get("/admin", dependencies=[Depends(get_admin)], response_class=HTMLResponse)
def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "ads": ads,
        "chats": chats,
        "payments": payments,
        "order_status": order_status,
        "balances": balances
    })

@app.post("/admin/ad/{ad_id}/delete", dependencies=[Depends(get_admin)])
def admin_del(ad_id: str):
    global ads
    ads = [ad for ad in ads if ad["id"] != ad_id]
    chats.pop(ad_id, None)
    payments.pop(ad_id, None)
    order_status.pop(ad_id, None)
    return RedirectResponse("/admin", 302)

@app.post("/admin/ad/{ad_id}/resolve", dependencies=[Depends(get_admin)])
def admin_res(ad_id: str):
    if order_status.get(ad_id) == "disputed":
        seller = payments[ad_id]["user"]
        balances[seller] = balances.get(seller, 0.0) + payments[ad_id]["cost"] * 0.99
        order_status[ad_id] = "released"
    return RedirectResponse("/admin", 302)
