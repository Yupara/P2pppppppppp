from fastapi import FastAPI, Request, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from typing import Optional

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Примитивная in-memory база
ads_db = []
orders_db = []

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads_db})

@app.get("/create-ad", response_class=HTMLResponse)
def create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create-ad", response_class=HTMLResponse)
def create_ad(
    request: Request,
    type: str = Form(...),
    amount: float = Form(...),
    currency: str = Form(...),
    payment_method: str = Form(...),
    price: float = Form(...)
):
    ad_id = str(uuid4())
    ad = {
        "id": ad_id,
        "type": type,
        "amount": amount,
        "currency": currency,
        "payment_method": payment_method,
        "price": price,
        "seller": "demo_seller"
    }
    ads_db.append(ad)
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade(request: Request, ad_id: str):
    ad = next((a for a in ads_db if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    return templates.TemplateResponse("trade.html", {"request": request, "ad": ad})
