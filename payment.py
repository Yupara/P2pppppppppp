# payment.py

from fastapi import (
    APIRouter, Request, Depends,
    Form, HTTPException
)
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import crud, models
from db import get_db
from auth import get_current_user

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@router.get("/market", response_class=HTMLResponse)
def market(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if user.is_blocked:
        warning = "Ваш аккаунт заблокирован из-за 10 отмен. Новые сделки недоступны."
    else:
        warning = None
    ads = db.query(models.Ad).all()
    return templates.TemplateResponse("market.html", {
        "request": request,
        "ads": ads,
        "user": user,
        "warning": warning
    })

@router.get("/create_order/{ad_id}")
def create_order(ad_id: int, request: Request,
    db: Session = Depends(get_get_db), user: models.User = Depends(get_current_user)
):
    if user.is_blocked:
        raise HTTPException(403, "Вы заблокированы")
    ad = db.query(models.Ad).get(ad_id)
    if not ad or ad.user_id == user.id:
        raise HTTPException(400, "Нельзя купить у себя или объявления нет")
    order = crud.create_order(db, ad, user)
    return RedirectResponse(f"/trade/{order.id}", status_code=302)

@router.get("/trade/{order_id}", response_class=HTMLResponse)
def trade_page(order_id: int, request: Request,
    db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    order = db.query(models.Order).get(order_id)
    if not order or (order.buyer_id != user.id and order.ad.user_id != user.id):
        raise HTTPException(404, "Сделка не найдена")
    messages = crud.get_messages(db, order_id)
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "order": order,
        "messages": messages,
        "user": user
    })

@router.post("/pay/{order_id}")
def pay(order_id: int, request: Request,
    db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    order = db.query(models.Order).get(order_id)
    try:
        crud.pay_order(db, order, user)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return RedirectResponse(f"/trade/{order_id}", status_code=302)

@router.post("/confirm/{order_id}")
def confirm(order_id: int, request: Request,
    db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    order = db.query(models.Order).get(order_id)
    admin = db.query(models.User).get(1)
    try:
        crud.confirm_order(db, order, user, admin)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return RedirectResponse("/orders/mine", status_code=302)

@router.post("/dispute/{order_id}")
def dispute(order_id: int, request: Request,
    db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    order = db.query(models.Order).get(order_id)
    try:
        crud.dispute_order(db, order, user)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return RedirectResponse(f"/trade/{order_id}", status_code=302)

@router.post("/message/{order_id}")
def message(order_id: int, text: str = Form(...), request: Request = None,
    db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    crud.add_message(db, order_id, user.id, text)
    return RedirectResponse(f"/trade/{order_id}", status_code=302)
