from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.message import Message
from schemas.message import MessageCreate, MessageOut
from utils.auth import get_current_user
from database import get_db

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/", response_model=MessageOut)
def send_message(msg: MessageCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    message = Message(
        order_id=msg.order_id,
        sender_id=user.id,
        content=msg.content
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

@router.get("/{order_id}", response_model=list[MessageOut])
def get_messages(order_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    messages = db.query(Message).filter(Message.order_id == order_id).order_by(Message.timestamp).all()
    return messages
