from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Временные хранилища
ads = []
messages = {}
statuses = {}

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/market")
def market_page(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

@app.get("/create-ad")
def create_ad_page(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create-ad")
def create_ad(request: Request, ad_type: str = Form(...), amount: str = Form(...), price: str = Form(...), payment: str = Form(...)):
    ad_id = str(uuid4())
    ads.append({
        "id": ad_id,
        "type": ad_type,
        "amount": amount,
        "price": price,
        "payment": payment
    })
    statuses[ad_id] = {"paid": False, "confirmed": False, "dispute": False}
    return RedirectResponse(url="/market", status_code=302)

@app.get("/trade/{ad_id}")
def trade_page(request: Request, ad_id: str):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        return RedirectResponse(url="/market", status_code=302)

    return templates.TemplateResponse("trade.html", {
        "request": request,
        "order_id": ad_id,
        "amount": ad["amount"],
        "price": ad["price"],
        "payment_method": ad["payment"],
        "messages": messages.get(ad_id, []),
        "status": statuses.get(ad_id, {})
    })

@app.post("/trade/{ad_id}/message")
def send_message(request: Request, ad_id: str, message: str = Form(...)):
    messages.setdefault(ad_id, []).append(message)
    return RedirectResponse(url=f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/paid")
def mark_paid(request: Request, ad_id: str):
    statuses[ad_id]["paid"] = True
    return RedirectResponse(url=f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/confirm")
def confirm_payment(request: Request, ad_id: str):
    statuses[ad_id]["confirmed"] = True
    return RedirectResponse(url=f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/dispute")
def open_dispute(request: Request, ad_id: str):
    statuses[ad_id]["dispute"] = True
    return RedirectResponse(url=f"/trade/{ad_id}", status_code=302)
