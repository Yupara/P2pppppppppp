# auth.py

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from db import get_db               # <-- сюда
import crud

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return HTMLResponse("<h1>Login Form</h1>")

@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)   # <-- из db.py
):
    user = crud.get_user(db, username)
    if not user or user.password != password:
        raise HTTPException(400, "Неверные данные")
    request.session["user_id"] = user.id
    return RedirectResponse("/market", status_code=302)
