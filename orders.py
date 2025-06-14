from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app import get_db, get_user_uuid
from models import Ad, Order

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/create/{ad_id}")
def create_order(
    ad_id: int,
    amount: float = Form(...),
    payment: str = Form(...),
    request: Request,
    db: Session = Depends(get_db)
):
    # проверяем объявление
    ad = db.query(Ad).get(ad_id)
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    # проверяем лимиты
    if amount < ad.min_limit or amount > ad.max_limit:
        raise HTTPException(400, f"Сумма должна быть между {ad.min_limit} и {ad.max_limit}")
    # проверяем, что метод оплаты допустим
    allowed = [m.strip() for m in ad.payment_methods.split(",")]
    if payment not in allowed:
        raise HTTPException(400, f"Метод оплаты должен быть из {allowed}")
    # создаём заказ
    order = Order(
        ad_id=ad.id,
        buyer_uuid=get_user_uuid(request),
        amount=amount,
        payment=payment,
        status="pending"
    )
    db.add(order)
    db.commit()
    return RedirectResponse(f"/trade/{order.id}", 302)
