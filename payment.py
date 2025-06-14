# payment.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import crud, models
from db import get_db
from auth import get_current_user, HTTPException, status

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@router.get("/market", response_class=HTMLResponse)
def market(
    request: Request,
    db: Session = Depends(get_db),
    # Попробуем получить пользователя, но не падаем, если нет сессии:
    user: models.User = Depends(get_current_user, use_cache=False)
):
    # Если внутри get_current_user случился 401 — поймаем его сами:
    warning = None
    try:
        # попытаемся проверить блокировку
        if user.is_blocked:
            warning = "Ваш аккаунт заблокирован из-за 10 отмен."
    except HTTPException as e:
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            user = None
        else:
            raise

    ads = db.query(models.Ad).all()
    return templates.TemplateResponse("market.html", {
        "request": request,
        "ads": ads,
        "user": user,       # либо User, либо None
        "warning": warning  # либо текст, либо None
    })
