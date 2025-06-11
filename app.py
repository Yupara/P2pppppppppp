from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Temporary in-memory databases
users = {}
ads = []
trades = []

# Supported currencies
CRYPTOS = ["usdt", "btc", "eth", "trump"]
FIATS = ["USD","EUR","GBP","RUB","UAH","KZT","TRY","AED","NGN","INR","VND",
         "BRL","ARS","COP","PEN","MXN","CLP","ZAR","EGP","GHS","KES","MAD",
         "PKR","BDT","LKR","IDR","THB","MYR","PHP","KRW","TJS"]

def get_user(request: Request):
    return request.session.get("user")

# Add middleware manually without actual secret; you can skip sessions:
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key="secret")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "user": get_user(request)})

@app.get("/register", response_class=HTMLResponse)
def reg_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "msg": ""})

@app.post("/register")
def reg_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if username in users:
        return templates.TemplateResponse("register.html", {"request": request, "msg": "User exists"})
    users[username] = password
    request.session["user"] = username
    return RedirectResponse("/", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "msg": ""})

@app.post("/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if users.get(username) == password:
        request.session["user"] = username
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "msg": "Invalid credentials"})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)

@app.get("/create_ad", response_class=HTMLResponse)
def create_ad_get(request: Request):
    if not get_user(request):
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("create_ad.html", {"request": request, "cryptos": CRYPTOS, "fiats": FIATS})

@app.post("/create_ad")
def create_ad_post(request: Request,
                   action: str = Form(...),
                   crypto: str = Form(...),
                   fiat: str = Form(...),
                   rate: float = Form(...),
                   amount: float = Form(...),
                   payment: str = Form(...)):
    ad = {
        "id": str(uuid4()),
        "user": get_user(request),
        "action": action,
        "crypto": crypto,
        "fiat": fiat,
        "rate": rate,
        "amount": amount,
        "payment": payment
    }
    ads.append(ad)
    return RedirectResponse("/market", status_code=302)

@app.get("/market", response_class=HTMLResponse)
def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads, "user": get_user(request)})

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade_get(request: Request, ad_id: str):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse("trade.html", {"request": request, "ad": ad, "user": get_user(request)})
