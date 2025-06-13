from fastapi import (
    APIRouter, Request, Depends,
    Form, HTTPException, status
)
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

import crud
from db import get_db  # <-- импорт из db.py

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return HTMLResponse("<h1>Login Form</h1>")

@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = crud.get_user(db, username)
    if not user or user.password != password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Неверные данные")
    request.session["user_id"] = user.id
    return RedirectResponse("/market", status_code=302)
