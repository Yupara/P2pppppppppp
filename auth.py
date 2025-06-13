# auth.py

from fastapi import (
    APIRouter, Request, Depends,
    Form, HTTPException, status
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import crud
import models
from db import get_db

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User)\
             .filter_by(username=username, password=password)\
             .first()
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request, "error": "Неверные данные"
        })
    if user.is_blocked:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Ваш аккаунт заблокирован из-за 10 отмен"
        })
    request.session["user_id"] = user.id
    return RedirectResponse("/market", status_code=302)
