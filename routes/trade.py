from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from starlette.datastructures import URL

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Храним сделки и сообщения в памяти
orders = {}
messages = {}

@router.get("/trade/{ad_id}")
def trade_page(request: Request, ad_id: str):
    order = orders.get(ad_id)
    if not order:
        return templates.TemplateResponse("trade.html", {
            "request": request,
            "order_id": ad_id,
            "amount": "100",
            "price": "1.0",
            "payment_method": "Tinkoff",
            "messages": [],
        })
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "order_id": ad_id,
        "amount": order["amount"],
        "price": order["price"],
        "payment_method": order["payment_method"],
        "messages": messages.get(ad_id, [])
    })

@router.post("/trade/{ad_id}/message")
def post_message(request: Request, ad_id: str, message: str = Form(...)):
    messages.setdefault(ad_id, []).append(message)
    return RedirectResponse(url=f"/trade/{ad_id}", status_code=302)
