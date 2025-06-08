from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.order import Order
from models.user import get_current_user

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("/{order_id}/mark_paid")
def mark_paid(order_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    if order.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="Вы не покупатель")
    order.status = "paid"
    db.commit()
    return {"detail": "Отмечено как оплачено"}


@router.post("/{order_id}/mark_confirmed")
def mark_confirmed(order_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    if order.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Вы не продавец")
    order.status = "confirmed"
    db.commit()
    return {"detail": "Отмечено как подтверждено"}

@router.post("/{order_id}/open_dispute")
def open_dispute(order_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    if order.buyer_id != user.id and order.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Вы не участник сделки")
    order.status = "dispute"
    db.commit()
    return {"detail": "Спор открыт"}
