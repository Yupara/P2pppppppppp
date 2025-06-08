from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.order import Order
from utils.auth import get_current_user

router = APIRouter(prefix="/api/orders", tags=["Orders"])

@router.post("/{order_id}/mark_paid")
def mark_order_paid(order_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    if order.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    order.status = "paid"
    db.commit()
    return {"message": "Сделка отмечена как оплаченная"}

@router.post("/{order_id}/confirm")
def confirm_order(order_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    if order.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    order.status = "confirmed"
    db.commit()
    return {"message": "Сделка подтверждена"}

@router.post("/{order_id}/dispute")
def dispute_order(order_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    if order.buyer_id != user.id and order.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    order.status = "disputed"
    db.commit()
    return {"message": "Открыт спор"}
