from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/trade/{order_id}", response_class=HTMLResponse)
async def trade_page(order_id: int, request: Request):
    return templates.TemplateResponse("trade.html", {"request": request, "order_id": order_id})
