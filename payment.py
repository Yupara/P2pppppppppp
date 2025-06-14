# payment.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import crud, models
from db import get_db

templates = Jinja2Templates(directory="templates")
router = APIRouter()


@router.get("/market", response_class=HTMLResponse)
def market(request: Request, db: Session = Depends(get_db)):
    """
    Публичная страница рынка — не требует авторизации.
    Если пользователь авторизован, в шаблоне будет
    доступен объект `request.session['user_id']` и можно
    получить его данные через отдельный запрос.
    """
    ads = db.query(models.Ad).all()
    return templates.TemplateResponse("market.html", {
        "request": request,
        "ads": ads,
        # шаблон может сам делать запрос за user по session, если нужно
    })
