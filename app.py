from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4

app = FastAPI()

# Статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ХРАНЕНИЕ ОБЪЯВЛЕНИЙ В ПАМЯТИ
ads = []

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "ads": ads})

@app.get("/create", response_class=HTMLResponse)
async def create_ad_page(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})

@app.post("/create")
async def create_ad(
    request: Request,
    type: str = Form(...),
    price: float = Form(...),
    amount: float = Form(...)
):
    ad = {
        "id": str(uuid4()),
        "type": type,
        "price": price,
        "amount": amount
    }
    ads.append(ad)
    return RedirectResponse(url="/", status_code=303)

@app.get("/order/{ad_id}", response_class=HTMLResponse)
async def view_order(request: Request, ad_id: str):
    ad = next((ad for ad in ads if ad["id"] == ad_id), None)
    if not ad:
        return HTMLResponse(content="Объявление не найдено", status_code=404)
    return templates.TemplateResponse("order.html", {"request": request, "ad": ad})
