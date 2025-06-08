from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.status import HTTP_302_FOUND

from database import get_db
from models import Ad, User
from utils.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/ads", response_class=HTMLResponse)
def list_ads(request: Request, db: Session = Depends(get_db)):
    """Список всех активных объявлений"""
    ads = db.query(Ad).filter(Ad.is_active == True).all()
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})


@router.get("/ads/my", response_class=HTMLResponse)
def my_ads(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Список объявлений текущего пользователя"""
    ads = db.query(Ad).filter(Ad.owner_id == current_user.id).all()
    return templates.TemplateResponse("seller.html", {"request": request, "ads": ads})


@router.get("/ads/create", response_class=HTMLResponse)
def create_ad_form(request: Request, current_user: User = Depends(get_current_user)):
    """Форма создания нового объявления"""
    return templates.TemplateResponse("create_ad.html", {"request": request})


@router.post("/ads/create")
def create_ad(
    request: Request,
    type: str = Form(...),
    price: float = Form(...),
    amount: float = Form(...),
    currency: str = Form(...),
    payment_method: str = Form(...),
    min_limit: float = Form(...),
    max_limit: float = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обработка создания объявления"""
    ad = Ad(
        type=type,
        price=price,
        amount=amount,
        currency=currency,
        payment_method=payment_method,
        min_limit=min_limit,
        max_limit=max_limit,
        owner_id=current_user.id
    )
    db.add(ad)
    db.commit()
    db.refresh(ad)
    return RedirectResponse(url="/ads/my", status_code=HTTP_302_FOUND)


@router.post("/ads/{ad_id}/deactivate")
def deactivate_ad(ad_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Деактивация (удаление) объявления"""
    ad = db.query(Ad).filter(Ad.id == ad_id, Ad.owner_id == current_user.id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    ad.is_active = False
    db.commit()
    return RedirectResponse(url="/ads/my", status_code=HTTP_302_FOUND)
