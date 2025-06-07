from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.order import Order, OrderStatus
from schemas.order import OrderCreate, OrderOut
from database import get_db
from utils.auth import get_current_user

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.post("/", response_model=OrderOut)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = Order(
        ad_id=order_data.ad_id,
        amount=order_data.amount,
        price=order_data.price,
        type=order_data.type,
        user_id=user.id,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.get("/mine", response_model=list[OrderOut])
def get_my_orders(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Order).filter(Order.user_id == user.id).all()

@router.post("/{order_id}/status/{new_status}")
def update_order_status(order_id: int, new_status: OrderStatus, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = new_status
    db.commit()
    return {"message": "Order status updated"}
