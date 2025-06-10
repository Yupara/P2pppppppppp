from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List
from uuid import uuid4

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Простая база объявлений в памяти
ads_db = []

@router.get("/ads/create")
def show_create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@router.post("/ads/create")
def create_ad(
    request: Request,
    type: str = Form(...),
    amount: float = Form(...),
    price: float = Form(...),
    payment_method: str = Form(...)
):
    ad = {
        "id": str(uuid4()),
        "type": type,
        "amount": amount,
        "price": price,
        "payment_method": payment_method
    }
    ads_db.append(ad)
    return RedirectResponse(url="/market", status_code=302)

@router.get("/market")
def show_market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads_db})
