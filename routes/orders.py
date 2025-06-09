from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.status import HTTP_302_FOUND

from database import get_db
from models import User, Ad, Order, ChatMessage
from utils.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/orders/create/{ad_id}")
def confirm_create(ad_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Страница подтверждения покупки (можно убрать, делать сразу POST)
    ad = db.query(Ad).get(ad_id)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    return templates.TemplateResponse("confirm_create.html", {"request": request, "ad": ad})


@router.post("/orders/create/{ad_id}")
def create_order(ad_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ad = db.query(Ad).get(ad_id)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    order = Order(
        ad_id=ad.id,
        buyer_id=current_user.id,
        seller_id=ad.owner_id,
        amount=ad.amount,
        price=ad.price,
        status="pending"
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return RedirectResponse(f"/orders/{order.id}", status_code=HTTP_302_FOUND)


@router.get("/orders/{order_id}", response_class=HTMLResponse)
def view_order(order_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(404, "Сделка не найдена")
    # Загрузить историю чата
    messages = db.query(ChatMessage).filter(ChatMessage.order_id == order_id).order_by(ChatMessage.created_at).all()
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "order": order,
        "messages": messages,
        "user": current_user
    })


@router.post("/orders/{order_id}/mark_paid")
def mark_as_paid(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).get(order_id)
    if not order or order.buyer_id != current_user.id:
        raise HTTPException(403, "Нет доступа")
    order.status = "paid"
    db.add(ChatMessage(order_id=order.id, sender_id=current_user.id, content="Покупатель отметил оплату"))
    db.commit()
    return JSONResponse({"detail": "Отмечено как оплачено"})


@router.post("/orders/{order_id}/confirm")
def confirm_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).get(order_id)
    if not order or order.seller_id != current_user.id:
        raise HTTPException(403, "Нет доступа")
    order.status = "completed"
    db.add(ChatMessage(order_id=order.id, sender_id=current_user.id, content="Продавец подтвердил получение"))
    db.commit()
    return JSONResponse({"detail": "Сделка подтверждена"})


@router.post("/orders/{order_id}/dispute")
def open_dispute(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).get(order_id)
    if not order or (order.buyer_id != current_user.id and order.seller_id != current_user.id):
        raise HTTPException(403, "Нет доступа")
    order.status = "dispute"
    db.add(ChatMessage(order_id=order.id, sender_id=current_user.id, content="Открыт спор"))
    db.commit()
    return JSONResponse({"detail": "Спор открыт"})


@router.get("/orders/{order_id}/messages")
def get_messages(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    msgs = db.query(ChatMessage).filter(ChatMessage.order_id == order_id).order_by(ChatMessage.created_at).all()
    return [{"sender_username": msg.sender.username, "content": msg.content} for msg in msgs]


@router.post("/orders/{order_id}/messages")
def post_message(order_id: int, content: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).get(order_id)
    if not order or (current_user.id not in (order.buyer_id, order.seller_id)):
        raise HTTPException(403, "Нет доступа")
    msg = ChatMessage(order_id=order_id, sender_id=current_user.id, content=content["content"])
    db.add(msg)
    db.commit()
    return JSONResponse({"detail": "Сообщение отправлено"})

from utils.telegram import notify_admin

@router.post("/orders/{order_id}/dispute")
def open_dispute(...):
    # существующий код ...
    notify_admin(f"⚠️ <b>Спор открыт</b>\nСделка №{order_id}\nПользователь: {current_user.username}")
    return JSONResponse({"detail": "Спор открыт"})

@router.post("/orders/create/{ad_id}")
def create_order(...):
    # существующий код создания
    if order.amount * order.price >= 10000:
        notify_admin(f"💰 <b>Крупная сделка</b>\nСделка №{order.id}\nСумма: {order.amount} USDT × {order.price} ₽")
    return RedirectResponse(...)
