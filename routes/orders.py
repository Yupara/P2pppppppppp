from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.order import Order as OrderModel
from models.user import User as UserModel
from database import get_db
from schemas.order import OrderCreate, OrderResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from utils.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/orders", response_class=HTMLResponse)
def list_orders(request: Request, db: Session = Depends(get_db)):
    orders = db.query(OrderModel).filter(OrderModel.status == "open").all()
    return templates.TemplateResponse("orders.html", {"request": request, "orders": orders})


@router.get("/orders/mine", response_model=list[OrderResponse])
def my_orders(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    return db.query(OrderModel).filter(OrderModel.buyer_id == current_user.id).all()


@router.get("/orders/{order_id}", response_class=HTMLResponse)
def get_order_page(order_id: int, request: Request, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    return templates.TemplateResponse("trade.html", {"request": request, "order": order, "user": current_user})


@router.post("/orders/{order_id}/pay")
def mark_as_paid(order_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    order.status = "paid"
    db.commit()
    return {"detail": "Статус изменён на 'оплачено'"}


@router.post("/orders/{order_id}/confirm")
def confirm_payment(order_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    order.status = "confirmed"
    db.commit()
    return {"detail": "Платёж подтверждён"}


@router.post("/orders/{order_id}/dispute")
def open_dispute(order_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    order.status = "disputed"
    db.commit()
    return {"detail": "Открыт спор по сделке"}
