from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.status import HTTP_302_FOUND

from database import get_db
from models import User, Order
from utils.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/orders/mine")
def get_my_orders(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    orders = db.query(Order).filter((Order.buyer_id == current_user.id) | (Order.seller_id == current_user.id)).all()
    
    result = []
    for order in orders:
        result.append({
            "id": order.id,
            "type": order.type,
            "amount": order.amount,
            "price": order.price,
            "status": order.status,
            "is_owner": order.seller_id == current_user.id
        })

    return templates.TemplateResponse("orders.html", {
        "request": request,
        "orders": result
    })


@router.post("/orders/{order_id}/mark_paid")
def mark_as_paid(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order and order.buyer_id == current_user.id:
        order.status = "paid"
        db.commit()
    return RedirectResponse(url="/orders/mine", status_code=HTTP_302_FOUND)


@router.post("/orders/{order_id}/confirm")
def confirm_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order and order.seller_id == current_user.id and order.status == "paid":
        order.status = "completed"
        db.commit()
    return RedirectResponse(url="/orders/mine", status_code=HTTP_302_FOUND)


@router.post("/orders/{order_id}/dispute")
def open_dispute(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order and (order.buyer_id == current_user.id or order.seller_id == current_user.id):
        order.status = "disputed"
        db.commit()
    return RedirectResponse(url="/orders/mine", status_code=HTTP_302_FOUND)
