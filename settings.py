from fastapi import (
    APIRouter, Request, Depends,
    Form, HTTPException
)
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from db import get_db
from auth import get_current_user
import models

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/settings", response_class=HTMLResponse)
def settings_form(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": user
    })

@router.post("/settings")
def settings_update(
    request: Request,
    card_number: str       = Form(None),
    card_holder: str       = Form(None),
    wallet_address: str    = Form(None),
    wallet_network: str    = Form(None),
    db: Session            = Depends(get_db),
    user: models.User      = Depends(get_current_user)
):
    if card_number is not None:
        user.card_number = card_number
    if card_holder is not None:
        user.card_holder = card_holder
    if wallet_address is not None:
        user.wallet_address = wallet_address
    if wallet_network is not None:
        user.wallet_network = wallet_network
    db.commit()
    return RedirectResponse("/settings", status_code=302)
