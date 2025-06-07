from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.order import Order
from models.user import User
from utils.auth import get_current_user

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.post("/{order_id}/mark-paid")
def mark_order_as_paid(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    if order.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    order.status = "paid"
    db.commit()
    return {"message": "Отмечено как оплачено"}

@router.post("/{order_id}/confirm-receipt")
def confirm_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    if order.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    order.status = "completed"
    db.commit()
    return {"message": "Сделка завершена"}

@router.post("/{order_id}/dispute")
def open_dispute(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    if user.id not in [order.buyer_id, order.seller_id]:
        raise HTTPException(status_code=403, detail="Нет доступа")
    order.status = "dispute"
    db.commit()
    return {"message": "Спор открыт"}
