from fastapi import (
    APIRouter, Request, Depends,
    Form, HTTPException, status
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
from db import get_db

templates = Jinja2Templates(directory="templates")
router = APIRouter()

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> models.User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован")
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    return user

@router.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@router.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(models.User).filter(models.User.username == username).first():
        return templates.TemplateResponse("register.html", {"request": request, "error": "Имя занято"})
    user = models.User(username=username, password=password)
    db.add(user); db.commit(); db.refresh(user)
    request.session["user_id"] = user.id
    return RedirectResponse("/market", status_code=302)

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
    user = db.query(models.User).filter_by(username=username, password=password).first()
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверные данные"})
    if user.is_blocked:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Аккаунт заблокирован"})
    request.session["user_id"] = user.id
    return RedirectResponse("/market", status_code=302)

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)
