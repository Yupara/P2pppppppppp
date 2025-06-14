from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app import get_db, get_user_uuid, templates, cancel_expired
from app import Ad, Trade, Message  # импорт моделей из app.py или из models.py

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/create/{ad_id}")
def create_order(
    ad_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    cancel_expired(db)
    ad = db.query(Ad).get(ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    user_uuid = get_user_uuid(request)
    if ad.uuid == user_uuid:
        raise HTTPException(status_code=400, detail="Нельзя купить у себя")
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
    return RedirectResponse(f"/orders/{trade.id}", status_code=302)

@router.get("/{trade_id}", response_class=HTMLResponse)
def view_order(
    trade_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    cancel_expired(db)
    trade = db.query(Trade).get(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    user_uuid = get_user_uuid(request)
    is_buyer  = trade.buyer_uuid == user_uuid
    is_seller = trade.ad.uuid   == user_uuid
    if not (is_buyer or is_seller):
        raise HTTPException(status_code=403, detail="Нет доступа")
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "trade": trade,
        "messages": trade.messages,
        "is_buyer": is_buyer,
        "is_seller": is_seller,
        "now": datetime.utcnow().isoformat()
    })

@router.post("/{trade_id}/paid")
def mark_paid(
    trade_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    t = db.query(Trade).get(trade_id)
    uu = get_user_uuid(request)
    if not t or t.buyer_uuid != uu or t.status != "pending":
        raise HTTPException(status_code=403)
    t.status = "paid"
    db.commit()
    return RedirectResponse(f"/orders/{trade_id}", status_code=302)

@router.post("/{trade_id}/confirm")
def mark_confirm(
    trade_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    t = db.query(Trade).get(trade_id)
    uu = get_user_uuid(request)
    if not t or t.ad.uuid != uu or t.status != "paid":
        raise HTTPException(status_code=403)
    t.status = "confirmed"
    db.commit()
    return RedirectResponse(f"/orders/{trade_id}", status_code=302)

@router.post("/{trade_id}/dispute")
def mark_dispute(
    trade_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    t = db.query(Trade).get(trade_id)
    uu = get_user_uuid(request)
    if not t or uu not in (t.buyer_uuid, t.ad.uuid):
        raise HTTPException(status_code=403)
    t.status = "disputed"
    db.commit()
    return RedirectResponse(f"/orders/{trade_id}", status_code=302)

@router.post("/{trade_id}/message")
def send_message(
    trade_id: int,
    request: Request,
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    t = db.query(Trade).get(trade_id)
    uu = get_user_uuid(request)
    if not t or uu not in (t.buyer_uuid, t.ad.uuid):
        raise HTTPException(status_code=403)
    msg = Message(
        trade_id=trade_id,
        sender_uuid=uu,
        content=content,
        timestamp=datetime.utcnow()
    )
    db.add(msg)
    db.commit()
    return RedirectResponse(f"/orders/{trade_id}", status_code=302)
