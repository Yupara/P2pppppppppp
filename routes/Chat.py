from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Trade, Message, User
from database import get_db
from auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.get("/{trade_id}")
def get_messages(trade_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade or user.id not in [trade.buyer_id, trade.ad.owner_id]:
        raise HTTPException(status_code=403, detail="Нет доступа")
    messages = db.query(Message).filter(Message.trade_id == trade_id).order_by(Message.timestamp).all()
    return [{"sender_id": m.sender_id, "content": m.content, "timestamp": m.timestamp.isoformat()} for m in messages]

@router.post("/{trade_id}")
def send_message(trade_id: int, content: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade or user.id not in [trade.buyer_id, trade.ad.owner_id]:
        raise HTTPException(status_code=403, detail="Нет доступа")
    message = Message(trade_id=trade_id, sender_id=user.id, content=content)
    db.add(message)
    db.commit()
    return {"status": "sent"}
