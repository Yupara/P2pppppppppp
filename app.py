from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uuid

app = FastAPI()

# Статика и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Хранилище объявлений (временно)
ads_db = []

# Главная
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Маркет
@app.get("/market", response_class=HTMLResponse)
async def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads_db})

# Создание объявления
@app.get("/create", response_class=HTMLResponse)
async def create_get(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create", response_class=HTMLResponse)
async def create_post(request: Request, type: str = Form(...), amount: float = Form(...), price: float = Form(...)):
    new_ad = {
        "id": str(uuid.uuid4()),
        "type": type,
        "amount": amount,
        "price": price
    }
    ads_db.append(new_ad)
    return RedirectResponse("/market", status_code=302)

# Сделка
@app.get("/trade/{ad_id}", response_class=HTMLResponse)
async def trade(request: Request, ad_id: str):
    ad = next((ad for ad in ads_db if ad["id"] == ad_id), None)
    if not ad:
        return HTMLResponse("Объявление не найдено", status_code=404)
    return templates.TemplateResponse("trade.html", {"request": request, "ad": ad})
