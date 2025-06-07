from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.order import Order
from utils.auth import get_current_user

router = APIRouter()

class ChatMessage(BaseModel):
    trade_id: int
    text: str

@router.post("/chat/send")
def send_chat_message(msg: ChatMessage, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == msg.trade_id).first()
    if not order or (order.buyer_id != user.id and order.seller_id != user.id):
        raise HTTPException(status_code=403, detail="Нет доступа к сделке")
    # Можно сохранить в таблицу messages, пока просто печатаем
    print(f"[Чат {msg.trade_id}] {user.username}: {msg.text}")
    return {"message": "Сообщение отправлено"}
