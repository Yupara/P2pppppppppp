from fastapi import FastAPI, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List
from uuid import uuid4
import uvicorn

app = FastAPI()

# Подключаем статику и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Простая "база" пользователей и объявлений
users = {}
ads = []

# Главная страница
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Страница регистрации
@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    if username in users:
        return {"error": "User already exists"}
    users[username] = {"password": password}
    response = RedirectResponse("/login", status_code=302)
    return response

# Страница логина
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = users.get(username)
    if not user or user["password"] != password:
        return {"error": "Invalid credentials"}
    response = RedirectResponse("/market", status_code=302)
    response.set_cookie(key="username", value=username)
    return response

# Маркет с объявлениями
@app.get("/market", response_class=HTMLResponse)
def market(request: Request):
    username = request.cookies.get("username")
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads, "username": username})

# Создание объявления
@app.get("/create_ad", response_class=HTMLResponse)
def create_ad_page(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create_ad")
def create_ad(
    request: Request,
    type: str = Form(...),
    amount: float = Form(...),
    currency: str = Form(...),
    payment_method: str = Form(...)
):
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse("/login", status_code=302)
    ad = {
        "id": str(uuid4()),
        "type": type,
        "amount": amount,
        "currency": currency,
        "payment_method": payment_method,
        "owner": username
    }
    ads.append(ad)
    return RedirectResponse("/market", status_code=302)

# Обработка сделки (нажатие кнопки "Купить")
@app.get("/buy/{ad_id}", response_class=HTMLResponse)
def buy_ad(ad_id: str, request: Request):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        return HTMLResponse("Ad not found", status_code=404)
    return templates.TemplateResponse("trade.html", {"request": request, "ad": ad})


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
