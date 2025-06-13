from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

import crud
from db import get_db  # <-- импорт из db.py

router = APIRouter()

@router.get("/market", response_class=HTMLResponse)
def market(request: Request, db: Session = Depends(get_db)):
    ads = crud.get_ads(db)
    # рендерьте ваш market.html, передавая ads
    return HTMLResponse("<h1>Market</h1>")
