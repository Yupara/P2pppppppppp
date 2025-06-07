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
