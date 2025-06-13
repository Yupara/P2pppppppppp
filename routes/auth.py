from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
import crud, schemas
from app import get_db

router = APIRouter()

@router.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@router.post("/register")
def register(request: Request, username: str = Form(...), password: str = Form(...),
             referral_code: str = Form(None), db: Session = Depends(get_db)):
    if crud.get_user(db, username):
        return templates.TemplateResponse("register.html", {"request": request, "error": "Имя занято"})
    user = crud.create_user(db, username, password, referral_code)
    # TODO: начислить бонус рефералу
    request.session["user_id"] = user.id
    return RedirectResponse("/market", status_code=302)

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...),
          db: Session = Depends(get_db)):
    user = crud.get_user(db, username)
    # TODO: проверить хеш
    if not user or user.password != password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверные данные"})
    request.session["user_id"] = user.id
    return RedirectResponse("/market", status_code=302)

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)
