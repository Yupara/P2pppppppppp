from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from uuid import uuid4

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class Ad:
    def __init__(self, id, type, price, currency, method):
        self.id = id
        self.type = type
        self.price = price
        self.currency = currency
        self.method = method

ads_db = []  # Простая база в памяти

@app.get("/", response_class=HTMLResponse)
def read_market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads_db})

@app.post("/ads/create")
def create_ad(
    request: Request,
    type: str = Form(...),
    price: float = Form(...),
    currency: str = Form(...),
    method: str = Form(...)
):
    ad = Ad(
        id=str(uuid4()),
        type=type,
        price=price,
        currency=currency,
        method=method
    )
    ads_db.append(ad)
    return RedirectResponse("/", status_code=302)
