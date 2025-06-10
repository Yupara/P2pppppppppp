from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from datetime import datetime

app = FastAPI()

# Подключаем статику и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Временное хранилище объявлений
ads = []

# Главная страница – список объявлений
@app.get("/", response_class=HTMLResponse)
async def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

# Страница создания объявления
@app.get("/create", response_class=HTMLResponse)
async def create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

# Обработка формы объявления
@app.post("/create")
async def create_ad(
    request: Request,
    username: str = Form(...),
    action: str = Form(...),
    amount: float = Form(...),
    payment_method: str = Form(...)
):
    ad = {
        "id": str(uuid4()),
        "username": username,
        "action": action,
        "amount": amount,
        "payment_method": payment_method,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    ads.append(ad)
    return RedirectResponse(url="/", status_code=302)
