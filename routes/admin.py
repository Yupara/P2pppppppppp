from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.status import HTTP_302_FOUND

from database import get_db
from models import User, Ad, Order
from utils.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")


def admin_only(user=Depends(get_current_user)):
    if not user.is_active or user.username != "admin":
        raise HTTPException(403, "Доступ запрещён")
    return user


@router.get("/", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db), admin=Depends(admin_only)):
    users = db.query(User).all()
    ads = db.query(Ad).all()
    orders = db.query(Order).all()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "users": users,
        "ads": ads,
        "orders": orders
    })


@router.post("/user/{user_id}/toggle")
def toggle_user(user_id: int, db: Session = Depends(get_db), admin=Depends(admin_only)):
    u = db.query(User).get(user_id)
    if u:
        u.is_active = not u.is_active
        db.commit()
    return RedirectResponse("/admin", HTTP_302_FOUND)


@router.post("/ad/{ad_id}/deactivate")
def deactivate_ad(ad_id: int, db: Session = Depends(get_db), admin=Depends(admin_only)):
    a = db.query(Ad).get(ad_id)
    if a:
        a.is_active = False
        db.commit()
    return RedirectResponse("/admin", HTTP_302_FOUND)


@router.post("/order/{order_id}/cancel")
def cancel_order(order_id: int, db: Session = Depends(get_db), admin=Depends(admin_only)):
    o = db.query(Order).get(order_id)
    if o:
        o.status = "cancelled"
        db.commit()
    return RedirectResponse("/admin", HTTP_302_FOUND)
