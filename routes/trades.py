from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import Trade, Ad, User
from auth import get_current_user

router = APIRouter(prefix="/trades", tags=["trades"])

class BuyRequest(BaseModel):
    ad_id: int
    amount: float

@router.post("/buy")
def buy_trade(request: BuyRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ad = db.query(Ad).filter(Ad.id == request.ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")

    if request.amount > ad.amount:
        raise HTTPException(status_code=400, detail="Недостаточно объёма в объявлении")

    trade = Trade(ad_id=ad.id, buyer_id=user.id, amount=request.amount)
    ad.amount -= request.amount  # уменьшаем доступное количество

    db.add(trade)
    db.commit()
    db.refresh(trade)

    return {"trade_id": trade.id}

@router.get("/my")
def get_my_trades(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trades = (
        db.query(Trade)
        .filter(Trade.buyer_id == user.id)
        .all()
    )

    return [
        {
            "trade_id": t.id,
            "ad_id": t.ad_id,
            "amount": t.amount,
        }
        for t in trades
    ]

@router.post("/{trade_id}/mark_paid")
def mark_trade_paid(trade_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    if trade.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")

    trade.status = "paid"
    db.commit()
    return {"message": "Статус сделки обновлён на 'paid'"}
