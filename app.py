from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("market.html", {"request": request})

@app.get("/market", response_class=HTMLResponse)
async def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request})

@app.get("/trade/{username}", response_class=HTMLResponse)
async def trade(request: Request, username: str):
    # Пример данных — позже подключим к базе
    user_data = {
        "username": username,
        "orders": 8,
        "rate": "100%",
        "avg_pay": "4 мин.",
        "avg_transfer": "1 мин.",
        "verified": True
    }
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "user": user_data
    })
