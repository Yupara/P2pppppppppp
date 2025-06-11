from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import User, Ad, Order, Message
from auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/create/{ad_id}")
def create_order(
    ad_id: int,
    amount: float = Form(...),
    payment: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        return {"error": "Объявление не найдено"}

    order = Order(
        buyer_id=current_user.id,
        seller_id=ad.owner_id,
        ad_id=ad.id,
        amount=amount,
        payment_method=payment,
        status="Ожидает оплаты",
        timestamp=datetime.utcnow(),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return RedirectResponse(url=f"/orders/trade/{order.id}", status_code=302)


@router.get("/trade/{order_id}")
def view_order(
    request: Request,
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"error": "Сделка не найдена"}

    ad = db.query(Ad).filter(Ad.id == order.ad_id).first()
    messages = db.query(Message).filter(Message.order_id == order.id).all()

    return templates.TemplateResponse(
        "trade.html",
        {
            "request": request,
            "order": order,
            "ad": ad,
            "messages": messages,
        },
    )


@router.post("/{order_id}/pay")
def mark_paid(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order and order.buyer_id == current_user.id:
        order.status = "Ожидает подтверждения"
        db.commit()
    return RedirectResponse(url=f"/orders/trade/{order.id}", status_code=302)


@router.post("/{order_id}/confirm")
def confirm_payment(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order and order.seller_id == current_user.id:
        order.status = "Завершено"
        db.commit()
    return RedirectResponse(url=f"/orders/trade/{order.id}", status_code=302)


@router.post("/{order_id}/dispute")
def open_dispute(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = "Спор"
        db.commit()
    return RedirectResponse(url=f"/orders/trade/{order.id}", status_code=302)


@router.post("/{order_id}/message")
def send_message(
    order_id: int,
    message: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_msg = Message(
        order_id=order_id,
        sender_id=current_user.id,
        content=message,
        timestamp=datetime.utcnow(),
    )
    db.add(new_msg)
    db.commit()
    return RedirectResponse(url=f"/orders/trade/{order_id}", status_code=302)


@router.get("/mine")
def my_orders(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    orders = db.query(Order).filter(
        (Order.buyer_id == current_user.id) | (Order.seller_id == current_user.id)
    ).order_by(Order.timestamp.desc()).all()
    return templates.TemplateResponse("orders.html", {"request": request, "orders": orders})
