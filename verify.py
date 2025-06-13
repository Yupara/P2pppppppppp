# verify.py

import os
import random
from fastapi import (
    APIRouter, Request, Depends,
    Form, UploadFile, File, HTTPException
)
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from db import get_db
from auth import get_current_user
import models

router = APIRouter()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/verify/phone", response_class=HTMLResponse)
def phone_form(request: Request, user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("verify_phone.html", {"request": request, "user": user, "error": None})


@router.post("/verify/phone")
def send_phone_code(
    request: Request,
    phone: str = Form(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    # генерируем код
    code = f"{random.randint(100000,999999)}"
    user.phone = phone
    user.phone_code = code
    db.commit()
    # TODO: здесь интегрировать реальную SMS-рассылку
    print(f"SMS code for {phone}: {code}")
    return RedirectResponse("/verify/phone/code", status_code=302)


@router.get("/verify/phone/code", response_class=HTMLResponse)
def code_form(request: Request, user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("verify_phone_code.html", {"request": request, "user": user, "error": None})


@router.post("/verify/phone/code")
def verify_phone_code(
    request: Request,
    code: str = Form(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    if user.phone_code != code:
        return templates.TemplateResponse("verify_phone_code.html", {
            "request": request, "user": user, "error": "Неверный код"
        })
    user.is_phone_verified = True
    user.phone_code = None
    db.commit()
    return RedirectResponse("/profile", status_code=302)


@router.get("/verify/passport", response_class=HTMLResponse)
def passport_form(request: Request, user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse("verify_passport.html", {"request": request, "user": user, "error": None})


@router.post("/verify/passport")
def upload_passport(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    ext = os.path.splitext(file.filename)[1]
    fname = f"{user.id}_{int(random.random()*1e9)}{ext}"
    path = os.path.join(UPLOAD_DIR, fname)
    with open(path, "wb") as f:
        f.write(file.file.read())
    user.passport_filename = fname
    user.is_passport_verified = False
    db.commit()
    return RedirectResponse("/profile", status_code=302)
