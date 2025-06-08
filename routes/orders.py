from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal
from models.order import Order

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/order/{order_id}", response_class=HTMLResponse)
def get_order_page(request: Request, order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Сделка не найдена")

    return templates.TemplateResponse("order.html", {
        "request": request,
        "order": {
            "id": order.id,
            "type": order.type,
            "amount": order.amount,
            "price": order.price,
            "status": order.status,
            "buyer_id": order.buyer_id,
            "seller_id": order.seller_id
        }
    })
