# admin.py

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
from db import get_db                    # <-- из db.py
from auth import get_current_user        # <-- из auth.py

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

def get_admin_user(
    user: models.User = Depends(get_current_user)
) -> models.User:
    if user.id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администратор"
        )
    return user

@router.get("", response_class=HTMLResponse)
def admin_dashboard(
    admin: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    # Здесь можно собрать данные для дашборда: 
    # споры, крупные сделки, статистику по комиссиям и т.д.
    # Например:
    disputes_count = db.query(models.Dispute).filter(models.Dispute.status == "open").count()
    large_trades = db.query(models.Order).filter(models.Order.amount >= 10000).count()
    total_commission = admin.commission_earned

    # Рендерим простой HTML (можете заменить на шаблон)
    html = f"""
    <h1>Admin Dashboard</h1>
    <p>Открытых споров: {disputes_count}</p>
    <p>Крупных сделок (>=10 000): {large_trades}</p>
    <p>Всего комиссии: {total_commission:.2f}</p>
    """
    return HTMLResponse(content=html)
