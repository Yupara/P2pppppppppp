from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models import Ad, Trade
from uuid import uuid4
from typing import Optional

app = FastAPI()

ads_db = []
trades_db = []

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/market", response_class=HTMLResponse)
def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads_db})

@app.get("/ads/create", response_class=HTMLResponse)
def create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/ads/create", response_class=HTMLResponse)
def create_ad(request: Request, type: str = Form(...), amount: float = Form(...), price: float = Form(...), payment: str = Form(...)):
    ad = Ad(id=str(uuid4()), type=type, amount=amount, price=price, payment=payment)
    ads_db.append(ad)
    return RedirectResponse(url="/market", status_code=status.HTTP_302_FOUND)

@app.get("/ads/{ad_id}/buy", response_class=HTMLResponse)
def buy_ad(request: Request, ad_id: str):
    ad = next((ad for ad in ads_db if ad.id == ad_id), None)
    if not ad:
        return HTMLResponse(content="Объявление не найдено", status_code=404)
    trade = Trade(id=str(uuid4()), ad=ad)
    trades_db.append(trade)
    return templates.TemplateResponse("trade.html", {"request": request, "trade": trade})
