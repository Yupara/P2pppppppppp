from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.order import Order
from models.user import User
from utils.auth import get_current_user

router = APIRouter()

@router.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    if order.buyer_id != user.id and order.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к сделке")
    return {
        "id": order.id,
        "type": order.type,
        "amount": order.amount,
        "price": order.price,
        "status": order.status
    }

@router.post("/orders/{order_id}/mark_paid")
def mark_order_paid(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    if order.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="Только покупатель может отметить оплату")
    order.status = "PAID"
    db.commit()
    return {"message": "Статус обновлён на PAID"}

@router.post("/orders/{order_id}/dispute")
def open_dispute(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    if order.buyer_id != user.id and order.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    order.status = "DISPUTE"
    db.commit()
    return {"message": "Спор открыт"}
