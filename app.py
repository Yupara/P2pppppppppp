from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Пример объявления
ads = [
    {
        "id": "1",
        "type": "buy",
        "amount": 100,
        "currency": "USDT",
        "price": 95,
        "payment_method": "Сбербанк"
    }
]

messages = [
    {"sender": "buyer", "content": "Привет, хочу купить"},
    {"sender": "seller", "content": "Окей, оплати сюда..."}
]

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade_page(request: Request, ad_id: str):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        return HTMLResponse("Объявление не найдено", status_code=404)
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "messages": messages
    })
