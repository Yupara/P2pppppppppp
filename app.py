from fastapi import FastAPI, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ==== Временные БД ====
users_db = {}
ads_db = []

# ==== Константы крипты и фиатов ====
CRYPTOCURRENCIES = ["usdt", "btc", "eth", "trump"]
FIATS = [
    "USD", "EUR", "GBP", "RUB", "UAH", "KZT", "TRY", "AED", "NGN", "INR", "VND", "BRL",
    "ARS", "COP", "PEN", "MXN", "CLP", "ZAR", "EGP", "GHS", "KES", "MAD", "PKR", "BDT",
    "LKR", "IDR", "THB", "MYR", "PHP", "KRW", "TJS"
]

# ==== Модели ====
class User(BaseModel):
    username: str
    password: str

class Ad(BaseModel):
    id: str
    user: str
    action: str  # buy/sell
    crypto: str
    fiat: str
    rate: float
    amount: float
    payment: str

# ==== Хелперы ====
def get_current_user(request: Request):
    username = request.session.get("user")
    if username and username in users_db:
        return users_db[username]
    return None

# ==== Маршруты ====

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if username in users_db:
        return RedirectResponse("/register", status_code=302)
    users_db[username] = {"username": username, "password": password}
    request.session["user"] = username
    return RedirectResponse("/", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    user = users_db.get(username)
    if user and user["password"] == password:
        request.session["user"] = username
        return RedirectResponse("/", status_code=302)
    return RedirectResponse("/login", status_code=302)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)

@app.get("/ads/create", response_class=HTMLResponse)
def create_ad_get(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("create_ad.html", {
        "request": request,
        "user": user,
        "cryptos": CRYPTOCURRENCIES,
        "fiats": FIATS
    })

@app.post("/ads/create")
def create_ad_post(
    request: Request,
    action: str = Form(...),
    crypto: str = Form(...),
    fiat: str = Form(...),
    rate: float = Form(...),
    amount: float = Form(...),
    payment: str = Form(...)
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    ad = Ad(
        id=str(uuid4()),
        user=user["username"],
        action=action,
        crypto=crypto,
        fiat=fiat,
        rate=rate,
        amount=amount,
        payment=payment
    )
    ads_db.append(ad)
    return RedirectResponse("/market", status_code=302)

@app.get("/market", response_class=HTMLResponse)
def market(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("market.html", {
        "request": request,
        "user": user,
        "ads": ads_db
    })

@app.get("/ads/{ad_id}", response_class=HTMLResponse)
def view_ad(request: Request, ad_id: str):
    user = get_current_user(request)
    ad = next((a for a in ads_db if a.id == ad_id), None)
    if not ad:
        return RedirectResponse("/market", status_code=302)
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "user": user,
        "ad": ad
    })

# ==== Фейковый продавец для тестов ====
users_db["seller"] = {"username": "seller", "password": "123456"}
ads_db.append(Ad(
    id=str(uuid4()),
    user="seller",
    action="sell",
    crypto="usdt",
    fiat="USD",
    rate=1.0,
    amount=1000.0,
    payment="Bank Transfer"
))
