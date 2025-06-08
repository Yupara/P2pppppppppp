from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os

app = FastAPI()

# Подключаем шаблоны и статические файлы
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

ORDERS_PATH = "data/dummy_orders.json"

def load_orders():
    if os.path.exists(ORDERS_PATH):
        with open(ORDERS_PATH, "r") as f:
            return json.load(f)
    return []

def save_orders(orders):
    with open(ORDERS_PATH, "w") as f:
        json.dump(orders, f, indent=2)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    orders = load_orders()
    return templates.TemplateResponse("index.html", {"request": request, "orders": orders})

@app.get("/trade/{order_id}", response_class=HTMLResponse)
async def trade_view(request: Request, order_id: str):
    orders = load_orders()
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        return HTMLResponse("Сделка не найдена", status_code=404)
    return templates.TemplateResponse("trade.html", {"request": request, "order": order})

@app.post("/mark_paid/{order_id}")
async def mark_paid(order_id: str):
    orders = load_orders()
    for o in orders:
        if o["id"] == order_id:
            o["status"] = "Оплачено"
            save_orders(orders)
            break
    return RedirectResponse(f"/trade/{order_id}", status_code=303)

@app.post("/confirm_payment/{order_id}")
async def confirm_payment(order_id: str):
    orders = load_orders()
    for o in orders:
        if o["id"] == order_id:
            o["status"] = "Завершено"
            save_orders(orders)
            break
    return RedirectResponse(f"/trade/{order_id}", status_code=303)

@app.post("/dispute/{order_id}")
async def dispute(order_id: str):
    orders = load_orders()
    for o in orders:
        if o["id"] == order_id:
            o["status"] = "Открыт спор"
            save_orders(orders)
            break
    return RedirectResponse(f"/trade/{order_id}", status_code=303)
