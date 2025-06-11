from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from datetime import datetime, timedelta

app = FastAPI()

# Статика и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory
ads = {}
# ads[ad_id] = {id, type, amount, price, payment_method}

@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse("/market")

@app.get("/market", response_class=HTMLResponse)
def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": list(ads.values())})

@app.get("/create", response_class=HTMLResponse)
def create_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create")
def create_ad(
    request: Request,
    type: str = Form(...),
    amount: float = Form(...),
    price: float = Form(...),
    payment_method: str = Form(...)
):
    ad_id = str(uuid4())
    ads[ad_id] = {
        "id": ad_id,
        "type": type,
        "amount": amount,
        "price": price,
        "payment_method": payment_method
    }
    return RedirectResponse("/market", status_code=302)

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade(request: Request, ad_id: str):
    ad = ads.get(ad_id)
    if not ad:
        return HTMLResponse("Объявление не найдено", status_code=404)
    # countdown 15 min
    end_time = datetime.utcnow() + timedelta(minutes=15)
    remaining = int((end_time - datetime.utcnow()).total_seconds())
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "remaining": remaining
    })
