from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from datetime import datetime, timedelta

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Временное хранилище объявлений
ads = []

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/market", response_class=HTMLResponse)
def market_page(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

@app.get("/create", response_class=HTMLResponse)
def create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create", response_class=HTMLResponse)
async def create_ad(request: Request):
    form = await request.form()
    ad = {
        "id": str(uuid4()),
        "type": form["type"],
        "amount": form["amount"],
        "currency": form["currency"],
        "fiat": form["fiat"],
        "payment_method": form["payment_method"],
        "min_limit": form["min_limit"],
        "max_limit": form["max_limit"],
        "seller": form["seller"],
    }
    ads.append(ad)
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade_page(ad_id: str, request: Request):
    ad = next((ad for ad in ads if ad["id"] == ad_id), None)
    if not ad:
        return HTMLResponse(content="Объявление не найдено", status_code=404)
    
    deadline = datetime.utcnow() + timedelta(minutes=15)
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "deadline": deadline.strftime("%Y-%m-%dT%H:%M:%S")
    })
