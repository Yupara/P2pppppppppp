from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from app import get_db, get_user_uuid
from app import Ad, Trade, Message  # импорт моделей из app.py
from datetime import datetime, timedelta

router = APIRouter(prefix="/orders", tags=["orders"])

# Помечаем просроченные сделки
def cancel_expired(db: Session):
    now = datetime.utcnow()
    expired = db.query(Trade).filter(
        Trade.status == "pending",
        Trade.expires_at <= now
    ).all()
    for t in expired:
        t.status = "canceled"
    db.commit()

@router.get("/create/{ad_id}")
def create_order(ad_id: int, request: Request, db: Session = Depends(get_db)):
    cancel_expired(db)
    ad = db.query(Ad).get(ad_id)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    user_uuid = get_user_uuid(request)
    if ad.uuid == user_uuid:
        raise HTTPException(400, "Нельзя купить у себя")
    trade = Trade(
        ad_id=ad.id,
        buyer_uuid=user_uuid,
        status="pending",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return RedirectResponse(f"/orders/trade/{trade.id}", status_code=302)

@router.get("/trade/{trade_id}", response_class=HTMLResponse)
def view_trade(trade_id: int, request: Request, db: Session = Depends(get_db)):
    cancel_expired(db)
    trade = db.query(Trade).get(trade_id)
    if not trade:
        raise HTTPException(404, "Сделка не найдена")
    user_uuid = get_user_uuid(request)
    is_buyer  = (trade.buyer_uuid == user_uuid)
    is_seller = (trade.ad.uuid    == user_uuid)
    if not (is_buyer or is_seller):
        raise HTTPException(403, "Нет доступа к этой сделке")
    messages = db.query(Message).filter(Message.trade_id == trade_id).all()
    return HTMLResponse(
        content=  
            # рендерим шаблон через Jinja2Templates уже в app.py –
            # здесь только передаём контекст
            request.app.extra["templates"].TemplateResponse(
                "trade.html",
                {
                    "request": request,
                    "trade": trade,
                    "messages": messages,
                    "is_buyer": is_buyer,
                    "is_seller": is_seller,
                    "now": datetime.utcnow().isoformat()
                }
            )
    )

@router.post("/trade/{trade_id}/paid")
def mark_paid(trade_id: int, request: Request, db: Session = Depends(get_db)):
    trade = db.query(Trade).get(trade_id)
    user_uuid = get_user_uuid(request)
    if not trade or trade.buyer_uuid != user_uuid or trade.status != "pending":
        raise HTTPException(403, "Нельзя отметить как оплачено")
    trade.status = "paid"
    db.commit()
    return RedirectResponse(f"/orders/trade/{trade_id}", status_code=302)

@router.post("/trade/{trade_id}/confirm")
def mark_confirm(trade_id: int, request: Request, db: Session = Depends(get_db)):
    trade = db.query(Trade).get(trade_id)
    user_uuid = get_user_uuid(request)
    if not trade or trade.ad.uuid != user_uuid or trade.status != "paid":
        raise HTTPException(403, "Нельзя подтвердить получение")
    trade.status = "confirmed"
    db.commit()
    return RedirectResponse(f"/orders/trade/{trade_id}", status_code=302)

@router.post("/trade/{trade_id}/dispute")
def mark_dispute(trade_id: int, request: Request, db: Session = Depends(get_db)):
    trade = db.query(Trade).get(trade_id)
    user_uuid = get_user_uuid(request)
    if not trade or user_uuid not in (trade.buyer_uuid, trade.ad.uuid):
        raise HTTPException(403, "Нет доступа")
    trade.status = "disputed"
    db.commit()
    return RedirectResponse(f"/orders/trade/{trade_id}", status_code=302)

@router.post("/trade/{trade_id}/message")
def send_message(
    trade_id: int,
    request: Request,
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    trade = db.query(Trade).get(trade_id)
    user_uuid = get_user_uuid(request)
    if not trade or user_uuid not in (trade.buyer_uuid, trade.ad.uuid):
        raise HTTPException(403, "Нет доступа")
    msg = Message(
        trade_id=trade_id,
        sender_uuid=user_uuid,
        content=content,
        timestamp=datetime.utcnow()
    )
    db.add(msg)
    db.commit()
    return RedirectResponse(f"/orders/trade/{trade_id}", status_code=302)
