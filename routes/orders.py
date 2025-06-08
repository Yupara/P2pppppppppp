from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from uuid import uuid4

router = APIRouter()

# Временные базы
orders_db = {}
chat_db = {}

# Зависимость — "текущий пользователь" (заглушка)
def get_current_user():
    return "testuser"  # Здесь должна быть авторизация через токен

# Модель сделки
class Order(BaseModel):
    id: str
    type: str  # "buy" или "sell"
    amount: float
    price: float
    buyer: str
    seller: str
    status: str  # "pending", "paid", "confirmed", "disputed"

# Модель сообщения
class Message(BaseModel):
    sender: str
    text: str

# Получение сделки
@router.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str, user=Depends(get_current_user)):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    return orders_db[order_id]

# Отметить как оплачено
@router.post("/api/orders/{order_id}/paid")
def mark_paid(order_id: str, user=Depends(get_current_user)):
    order = orders_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    order.status = "paid"
    return {"detail": "Отмечено как оплачено"}

# Подтвердить получение
@router.post("/api/orders/{order_id}/confirm")
def mark_confirmed(order_id: str, user=Depends(get_current_user)):
    order = orders_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    order.status = "confirmed"
    return {"detail": "Подтверждено"}

# Открыть спор
@router.post("/api/orders/{order_id}/dispute")
def mark_dispute(order_id: str, user=Depends(get_current_user)):
    order = orders_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    order.status = "disputed"
    return {"detail": "Спор открыт"}

# Получение чата
@router.get("/api/orders/{order_id}/chat", response_model=List[Message])
def get_chat(order_id: str, user=Depends(get_current_user)):
    return chat_db.get(order_id, [])

# Отправка сообщения
@router.post("/api/orders/{order_id}/chat")
def send_message(order_id: str, message: Message, user=Depends(get_current_user)):
    if order_id not in chat_db:
        chat_db[order_id] = []
    chat_db[order_id].append(message)
    return {"detail": "Сообщение отправлено"}

# Для теста: создать фейковую сделку
@router.post("/api/orders/create_test")
def create_test_order(user=Depends(get_current_user)):
    order_id = str(uuid4())
    new_order = Order(
        id=order_id,
        type="buy",
        amount=100.0,
        price=90_000.0,
        buyer=user,
        seller="seller123",
        status="pending"
    )
    orders_db[order_id] = new_order
    return {"id": order_id}
