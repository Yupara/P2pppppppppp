# payment.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

import crud
from db import get_db

router = APIRouter()

@router.get("/market", response_class=HTMLResponse)
def market(request: Request, db: Session = Depends(get_db)):
    ads = crud.get_ads(db)
    # Здесь вы можете рендерить шаблон, но хотя бы для теста:
    return HTMLResponse("<h1>Рынок P2P</h1>")
