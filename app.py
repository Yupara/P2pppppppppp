from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional, List
from pydantic import BaseModel
from uuid import uuid4

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Временные базы
users_db = {}
ads_db = []
orders_db = []
chat_db = {}

# Модели
class Ad(BaseModel):
    id: str
    type: str
    price: float
    currency: str
    method: str
    user: str

class Order(BaseModel):
    id: str
    ad_id: str
    buyer: str
    seller: str
    status: str
    chat: List[str] = []

# Авторизация
@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(request: Request, username: str = Form(...), password: str = Form(...)):
    if username in users_db:
        return HTMLResponse("User exists", status_code=400)
    users_db[username] = {"username": username, "password": password}
    return RedirectResponse("/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = users_db.get(username)
    if not user or user["password"] != password:
        return HTMLResponse("Invalid login", status_code=401)
    response = RedirectResponse("/", status_code=302)
    response.set_cookie("user", username)
    return response

def get_current_user(request: Request) -> Optional[str]:
    return request.cookies.get("user")

# Главная
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("base.html", {"request": request, "user": user})

# Рынок
@app.get("/market", response_class=HTMLResponse)
def market(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads_db, "user": user})

# Создание объявления
@app.post("/ads/create")
def create_ad(request: Request, type: str = Form(...), price: float = Form(...), currency: str = Form(...), method: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    ad = Ad(id=str(uuid4()), type=type, price=price, currency=currency, method=method, user=user)
    ads_db.append(ad)
    return RedirectResponse("/market", status_code=302)

# Сделка
@app.get("/buy/{ad_id}", response_class=HTMLResponse)
def buy_ad(request: Request, ad_id: str):
    buyer = get_current_user(request)
    ad = next((a for a in ads_db if a.id == ad_id), None)
    if not buyer or not ad:
        return HTMLResponse("Not found", status_code=404)
    order = Order(id=str(uuid4()), ad_id=ad.id, buyer=buyer, seller=ad.user, status="waiting")
    orders_db.append(order)
    chat_db[order.id] = []
    return RedirectResponse(f"/trade/{order.id}", status_code=302)

# Страница сделки
@app.get("/trade/{order_id}", response_class=HTMLResponse)
def trade_page(request: Request, order_id: str):
    user = get_current_user(request)
    order = next((o for o in orders_db if o.id == order_id), None)
    if not order or user not in [order.buyer, order.seller]:
        return HTMLResponse("Access denied", status_code=403)
    messages = chat_db.get(order.id, [])
    return templates.TemplateResponse("trade.html", {
        "request": request, "order": order, "user": user, "messages": messages
    })

# Чат
@app.post("/trade/{order_id}/chat")
def send_message(request: Request, order_id: str, message: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    chat_db[order_id].append(f"{user}: {message}")
    return RedirectResponse(f"/trade/{order_id}", status_code=302)

# Оплатил / Подтвердил / Спор
@app.post("/trade/{order_id}/action")
def update_status(request: Request, order_id: str, action: str = Form(...)):
    user = get_current_user(request)
    order = next((o for o in orders_db if o.id == order_id), None)
    if not order or user not in [order.buyer, order.seller]:
        return HTMLResponse("Access denied", status_code=403)

    if action == "paid" and user == order.buyer:
        order.status = "paid"
    elif action == "confirm" and user == order.seller:
        order.status = "confirmed"
    elif action == "dispute":
        order.status = "dispute"

    return RedirectResponse(f"/trade/{order_id}", status_code=302)

# Мои сделки
@app.get("/orders/mine", response_class=HTMLResponse)
def my_orders(request: Request):
    user = get_current_user(request)
    my = [o for o in orders_db if o.buyer == user or o.seller == user]
    return templates.TemplateResponse("orders.html", {"request": request, "orders": my, "user": user})
