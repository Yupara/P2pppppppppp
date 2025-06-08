from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import Order, User
from utils.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/orders/{order_id}", response_class=HTMLResponse)
def view_order(order_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    
    counterparty_id = order.buyer_id if current_user.id != order.buyer_id else order.seller_id
    counterparty = db.query(User).filter(User.id == counterparty_id).first()

    return templates.TemplateResponse("deal.html", {
        "request": request,
        "order": order,
        "counterparty": counterparty,
        "current_user": current_user
    })


@router.post("/api/orders/{order_id}/paid")
def mark_as_paid(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or current_user.id != order.buyer_id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    order.status = "paid"
    db.commit()
    return {"message": "Отмечено как оплачено"}


@router.post("/api/orders/{order_id}/confirm")
def mark_as_confirmed(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or current_user.id != order.seller_id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    order.status = "completed"
    db.commit()
    return {"message": "Сделка подтверждена"}


@router.post("/api/orders/{order_id}/dispute")
def open_dispute(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    order.status = "dispute"
    db.commit()
    return {"message": "Спор открыт"}
