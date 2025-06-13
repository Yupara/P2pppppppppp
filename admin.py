# admin.py

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
from db import get_db                      # <-- из db.py
from auth import get_current_user          # <-- из auth.py

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_admin_user(
    request: Request,
    user: models.User = Depends(get_current_user),
) -> models.User:
    # Админ — первый зарегистрированный пользователь (id=1)
    if user.id != 1:
        raise HTTPException(status_code=403, detail="Только администратор")
    return user

@router.get("/admin/disputes", response_class=HTMLResponse)
def view_disputes(
    request: Request,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_admin_user)
):
    disputes = (
        db.query(models.Dispute)
          .filter(models.Dispute.status == "open")
          .order_by(models.Dispute.created_at.desc())
          .all()
    )
    return templates.TemplateResponse("admin_disputes.html", {
        "request": request,
        "disputes": disputes,
        "admin": admin
    })

@router.post("/admin/disputes/{order_id}/resolve")
def resolve_dispute(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_admin_user)
):
    dispute = db.query(models.Dispute).get(order_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Спор не найден")
    dispute.status = "resolved"
    # При необходимости, обновите и заказ:
    order = db.query(models.Order).get(dispute.order_id)
    order.status = "confirmed"
    db.commit()
    return RedirectResponse(url="/admin/disputes", status_code=302)

@router.get("/admin/passports", response_class=HTMLResponse)
def pending_passports(
    request: Request,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_admin_user)
):
    users = (
        db.query(models.User)
          .filter(
              models.User.passport_filename != None,
              models.User.is_passport_verified == False
          )
          .all()
    )
    return templates.TemplateResponse("admin_passports.html", {
        "request": request,
        "users": users,
        "admin": admin
    })

@router.post("/admin/passports/{user_id}/approve")
def approve_passport(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_admin_user)
):
    u = db.query(models.User).get(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    u.is_passport_verified = True
    db.commit()
    return RedirectResponse(url="/admin/passports", status_code=302)
