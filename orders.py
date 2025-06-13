# orders.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from db import get_db
from auth import get_current_user
import models

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/orders/mine", response_class=HTMLResponse)
def my_orders(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    buy_orders = db.query(models.Order)\
                   .filter(models.Order.buyer_id == user.id)\
                   .order_by(models.Order.id.desc())\
                   .all()
    sell_orders = db.query(models.Order)\
                    .join(models.Ad)\
                    .filter(models.Ad.user_id == user.id)\
                    .order_by(models.Order.id.desc())\
                    .all()
    return templates.TemplateResponse("orders.html", {
        "request": request,
        "user": user,
        "buy_orders": buy_orders,
        "sell_orders": sell_orders
    })
