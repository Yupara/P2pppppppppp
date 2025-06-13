# auth.py

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

import crud
from db import get_db

router = APIRouter()

@router.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return HTMLResponse("<h1>Регистрация</h1>")

@router.post("/register")
def register(request: Request, username: str = Form(...), password: str = Form(...),
             db: Session = Depends(get_db)):
    crud.create_user(db, username, password)
    return RedirectResponse("/market", status_code=302)
