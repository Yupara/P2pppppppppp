from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from models import User, Ad, Order, Message
from database import get_db
from auth import get_current_user
from fastapi.templating import Jinja2Templates
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/orders/create/{ad_id}")
def create_order(
    ad_id: int,
    amount: float = Form(...),
    payment: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")

    order = Order(
        ad_id=ad.id,
        buyer_id=user.id,
        amount=amount,
        payment_method=payment,
        status="pending"
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return RedirectResponse(f"/trade/{ad.id}", status_code=303)


@router.get("/trade/{ad_id}")
def trade_page(ad_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")

    order = db.query(Order).filter(Order.ad_id == ad.id, Order.buyer_id == user.id).first()
    messages = db.query(Message).filter(Message.order_id == order.id).all() if order else []

    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "order": order,
        "messages": messages
    })


@router.post("/orders/{order_id}/pay")
def mark_as_paid(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or order.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    order.status = "paid"
    db.commit()
    return RedirectResponse(f"/trade/{order.ad_id}", status_code=303)


@router.post("/orders/{order_id}/confirm")
def confirm_receipt(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")

    ad = db.query(Ad).filter(Ad.id == order.ad_id).first()
    if not ad or ad.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    order.status = "completed"
    db.commit()
    return RedirectResponse(f"/trade/{order.ad_id}", status_code=303)


@router.post("/orders/{order_id}/dispute")
def open_dispute(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")

    ad = db.query(Ad).filter(Ad.id == order.ad_id).first()
    if not ad or (user.id != ad.owner_id and user.id != order.buyer_id):
        raise HTTPException(status_code=403, detail="Нет доступа к спору")

    order.status = "dispute"
    db.commit()
    return RedirectResponse(f"/trade/{order.ad_id}", status_code=303)


@router.post("/orders/{order_id}/message")
def send_message(
    order_id: int,
    message: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")

    msg = Message(
        order_id=order.id,
        sender_id=user.id,
        content=message,
        timestamp=datetime.utcnow()
    )
    db.add(msg)
    db.commit()

    return RedirectResponse(f"/trade/{order.ad_id}", status_code=303)
