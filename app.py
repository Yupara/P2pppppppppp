from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List
from fastapi.templating import Jinja2Templates
from fastapi import Request

# Мокаем базу данных
fake_orders_db = [
    {"user_id": 1, "type": "buy", "amount": 100, "price": 95_000, "status": "в ожидании"},
    {"user_id": 1, "type": "sell", "amount": 50, "price": 96_500, "status": "завершено"},
    {"user_id": 2, "type": "buy", "amount": 75, "price": 94_000, "status": "отменено"},
]

# Пример токен-авторизации
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

# CORS (разрешаем запросы с фронтенда)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разреши нужный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

class Order(BaseModel):
    type: str
    amount: float
    price: float
    status: str

# Простая фейковая функция получения пользователя
def get_current_user(token: str = Depends(oauth2_scheme)):
    # токен = "user1token" -> user_id = 1
    # токен = "user2token" -> user_id = 2
    if token == "user1token":
        return {"user_id": 1}
    elif token == "user2token":
        return {"user_id": 2}
    else:
        raise HTTPException(status_code=401, detail="Неверный токен")

# API: Вернуть сделки текущего пользователя
@app.get("/api/orders/mine", response_model=List[Order])
def get_my_orders(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    user_orders = [order for order in fake_orders_db if order["user_id"] == user_id]
    return user_orders

# HTML: Страница истории сделок
@app.get("/orders", response_class=HTMLResponse)
def orders_page(request: Request):
    return templates.TemplateResponse("orders.html", {"request": request})
