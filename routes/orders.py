from pydantic import BaseModel

class MessageCreate(BaseModel):
    content: str

@router.get("/orders/{order_id}/chat")
def get_chat(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = db.query(ChatMessage).filter(ChatMessage.order_id == order_id).all()
    return [{
        "content": m.content,
        "is_me": m.sender_id == current_user.id
    } for m in messages]

@router.post("/orders/{order_id}/chat")
def post_message(order_id: int, message: MessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_msg = ChatMessage(order_id=order_id, sender_id=current_user.id, content=message.content)
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return {"status": "ok"}

@router.post("/orders/{order_id}/mark_paid")
def mark_paid(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or order.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    order.status = "paid"
    db.commit()
    return {"status": "marked as paid"}

@router.post("/orders/{order_id}/mark_confirmed")
def mark_confirmed(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or order.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    order.status = "completed"
    db.commit()
    return {"status": "marked as confirmed"}

@router.post("/orders/{order_id}/dispute")
def dispute_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    order.status = "dispute"
    db.commit()
    return {"status": "dispute opened"}
