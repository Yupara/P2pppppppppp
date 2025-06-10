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

from fastapi import HTTPException

# Хранилище сделок и сообщений
orders = {}
messages = {}

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
async def trade_page(request: Request, ad_id: str):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    
    msg_list = messages.get(ad_id, [])
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "messages": msg_list
    })

@app.post("/trade/{ad_id}/chat")
async def send_message(ad_id: str, request: Request, message: str = Form(...)):
    if ad_id not in messages:
        messages[ad_id] = []
    messages[ad_id].append(message)
    return RedirectResponse(url=f"/trade/{ad_id}", status_code=302)
