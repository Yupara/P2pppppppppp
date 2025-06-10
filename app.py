from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Подключение папки со статикой и шаблонами
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Пример данных объявлений
ads_data = [
    {
        "owner_username": "Savak",
        "price": "70,96",
        "volume": "304,7685 USDT",
        "limits": "500 – 500 000 RUB",
        "orders": 40,
        "success_rate": 10,
        "payment_methods": ["SBP", "Кольнение"]
    },
    {
        "owner_username": "Ищу_Партнеров",
        "price": "71,03",
        "volume": "128,8821 USDT",
        "limits": "500 – 500 000 RUB",
        "orders": 15,
        "success_rate": 10,
        "payment_methods": ["Пиметы", "Овроеол"]
    },
    {
        "owner_username": "ПроданоМейкеро",
        "price": "71,03",
        "volume": "100,0000 USDT",
        "limits": "500 – 500 000 RUB",
        "orders": 11,
        "success_rate": 10,
        "payment_methods": ["SBP"]
    }
]

# Главная страница — рынок объявлений
@app.get("/", response_class=HTMLResponse)
async def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads_data})

# Страница сделки /trade/username
@app.get("/trade/{username}", response_class=HTMLResponse)
async def open_trade(username: str, request: Request):
    user_data = {
        "username": username,
        "orders": 8,
        "success_rate": "100%",
        "avg_transfer": "1 мин.",
        "avg_pay": "4 мин.",
    }
    return templates.TemplateResponse("trade.html", {"request": request, "user": user_data})
