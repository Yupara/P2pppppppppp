from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from uuid import uuid4

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Временное хранилище объявлений
class Ad(BaseModel):
    id: str
    type: str  # buy или sell
    asset: str
    price: float
    payment_method: str
    available: float

ads = []  # список всех объявлений

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

@app.get("/create-ad")
def create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create-ad")
def create_ad(
    request: Request,
    type: str = Form(...),
    asset: str = Form(...),
    price: float = Form(...),
    payment_method: str = Form(...),
    available: float = Form(...)
):
    ad = Ad(
        id=str(uuid4()),
        type=type,
        asset=asset,
        price=price,
        payment_method=payment_method,
        available=available
    )
    ads.append(ad)
    return RedirectResponse("/", status_code=303)

@app.get("/trade/{ad_id}")
def trade(request: Request, ad_id: str):
    ad = next((item for item in ads if item.id == ad_id), None)
    if not ad:
        return templates.TemplateResponse("404.html", {"request": request})
    return templates.TemplateResponse("trade.html", {"request": request, "ad": ad})
