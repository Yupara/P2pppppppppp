from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app import get_db, get_current_user
from models import Trade, Ad
from schemas import TradeCreate
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from datetime import datetime

router = APIRouter(prefix="/trade")
templates = Jinja2Templates(directory="templates")

@router.post("/{ad_id}")
def create_trade(ad_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    
    trade = Trade(
        buyer_id=user.id,
        ad_id=ad.id,
        amount=ad.amount,
        status="pending",
        created_at=datetime.utcnow()
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return {"trade_id": trade.id, "redirect": f"/trade/{trade.id}"}

@router.get("/{trade_id}", response_class=HTMLResponse)
def get_trade(trade_id: int, request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(404, "Сделка не найдена")
    return templates.TemplateResponse("trade.html", {"request": request, "trade": trade, "user": user})
