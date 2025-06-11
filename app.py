from fastapi import FastAPI, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from uuid import uuid4

from models import User, Ad, Order, get_db
from auth import get_current_user

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.post("/orders/create/{ad_id}", response_class=HTMLResponse)
def create_order(
    request: Request,
    ad_id: int,
    amount: float = Form(...),
    payment: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        return templates.TemplateResponse("error.html", {"request": request, "msg": "Объявление не найдено"})

    if ad.owner_id == user.id:
        return templates.TemplateResponse("error.html", {"request": request, "msg": "Нельзя создать сделку с самим собой"})

    new_order = Order(
        ad_id=ad.id,
        buyer_id=user.id,
        seller_id=ad.owner_id,
        amount=amount,
        payment_method=payment,
        status="pending"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return RedirectResponse(f"/trade/{new_order.id}", status_code=302)
