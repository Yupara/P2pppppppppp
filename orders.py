from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from uuid import UUID
from starlette.requests import Request
from starlette.responses import RedirectResponse

from models import User, Ad, Order
from schemas import OrderCreate
from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])

# ✅ Просмотр своих ордеров
@router.get("/mine", response_class=HTMLResponse)
def my_orders(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    orders = db.query(Order).filter(Order.buyer_id == user.id).all()
    return request.app.templates.TemplateResponse("orders.html", {"request": request, "orders": orders})


# ✅ Создание сделки
@router.post("/create/{ad_id}")
def create_order(ad_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    if ad.user_id == user.id:
        raise HTTPException(status_code=400, detail="Нельзя создать сделку с самим собой")

    order = Order(ad_id=ad.id, buyer_id=user.id, seller_id=ad.user_id)
    db.add(order)
    db.commit()
    db.refresh(order)

    return RedirectResponse(f"/orders/{order.id}", status_code=302)


# ✅ Страница сделки
@router.get("/{order_id}", response_class=HTMLResponse)
def order_detail(order_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")

    if user.id not in [order.buyer_id, order.seller_id]:
        raise HTTPException(status_code=403, detail="Нет доступа к сделке")

    return request.app.templates.TemplateResponse("trade.html", {"request": request, "order": order, "user": user})
