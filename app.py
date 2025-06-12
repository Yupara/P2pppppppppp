# app.py
from fastapi import (
    FastAPI, Request, Form, UploadFile, File,
    Depends, HTTPException, status
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import RedirectResponse as StarletteRedirect
from passlib.context import CryptContext
from uuid import uuid4
from datetime import datetime, timedelta
import secrets, os

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="ВАШ_СЕКРЕТ_ДЛЯ_СЕССИЙ")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBasic()

# In-memory
users = {}       # username -> {email, hashed_password}
ads = []         # объявления
chats = {}       # ad_id -> сообщения
payments = {}    # ad_id -> платёж
order_status = {}
blocked_until = {}
cancellations = {}
balances = {}

# 1) Exception handler: при 401 — редирект на /login
@app.exception_handler(HTTPException)
async def auth_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return StarletteRedirect(url="/login")
    return HTMLResponse(str(exc.detail), status_code=exc.status_code)

# 2) Auth helpers
def hash_pw(pw: str) -> str:
    return pwd_ctx.hash(pw)
def verify_pw(pw: str, hashed: str) -> bool:
    return pwd_ctx.verify(pw, hashed)

def get_current_user(request: Request) -> str:
    user = request.session.get("user")
    if not user or user not in users:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Не авторизован")
    return user

# 3) Admin BasicAuth
ADMIN_USER = "admin"
ADMIN_PASS = "МойСуперПароль123"
def get_admin(creds: HTTPBasicCredentials = Depends(security)):
    if not (
        secrets.compare_digest(creds.username, ADMIN_USER)
        and secrets.compare_digest(creds.password, ADMIN_PASS)
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверные учётные данные",
                            headers={"WWW-Authenticate":"Basic"})
    return creds.username

def check_block(user: str):
    until = blocked_until.get(user)
    if until and datetime.utcnow() < until:
        raise HTTPException(403, f"Заблокирован до {until}")

# ---- Routes ----
@app.get("/", response_class=RedirectResponse)
def root(): return RedirectResponse("/market", 302)

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
        return templates.TemplateResponse("register.html",
            {"request": request, "error": "Пользователь уже существует"})
    if password != password2:
        return templates.TemplateResponse("register.html",
            {"request": request, "error": "Пароли не совпадают"})
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
        return templates.TemplateResponse("login.html",
            {"request": request, "error": "Неверный логин или пароль"})
    request.session["user"] = username
    balances.setdefault(username, 1000.0)
    return RedirectResponse("/market", 302)

# Logout
@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", 302)

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
        "id": ad_id, "action": action, "crypto": crypto, "fiat": fiat,
        "rate": rate, "amount": amount, "min_limit": min_limit,
        "max_limit": max_limit, "payment_method": payment_method,
        "comment": comment, "owner": full_name, "card_number": card_number,
        "completed_orders": 55, "rating": 99
    })
    chats[ad_id] = []
    payments[ad_id] = {}
    order_status[ad_id] = None
    return RedirectResponse("/market", 302)

# Trade page & actions...
@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade_page(request: Request, ad_id: str, user: str = Depends(get_current_user)):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad: raise HTTPException(404, "Объявление не найдено")
    return templates.TemplateResponse("trade.html", {
        "request": request, "ad": ad, "messages": chats.get(ad_id, []),
        "status": order_status.get(ad_id), "balances": balances,
        "current_user": user, "blocked_until": blocked_until.get(user),
        "remaining": 15*60, "now": datetime.utcnow
    })

# (Остальные /trade/{ad_id}/buy, /pay, /confirm, /cancel, /dispute, /message как раньше...)

# Deposit/Withdraw/Profile/Admin — как было в прошлом примере, без изменений.
