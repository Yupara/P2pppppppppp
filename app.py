from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Временная база объявлений
ads = []

# Главная страница с объявлениями
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

# Страница создания объявления
@app.get("/create_ad", response_class=HTMLResponse)
def create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

# Обработка формы создания объявления
@app.post("/create_ad")
def create_ad(
    type: str = Form(...),
    currency: str = Form(...),
    amount: float = Form(...),
    fiat: str = Form(...),
    payment_method: str = Form(...),
    min_limit: float = Form(...),
    max_limit: float = Form(...)
):
    ad = {
        "id": str(uuid4()),
        "type": type,
        "currency": currency,
        "amount": amount,
        "fiat": fiat,
        "payment_method": payment_method,
        "min_limit": min_limit,
        "max_limit": max_limit,
        "seller": "TestUser"
    }
    ads.append(ad)
    return RedirectResponse("/", status_code=302)
