from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

router = APIRouter()
templates = Jinja2Templates(directory="templates")

fake_orders = {
    1: {"type": "buy", "amount": 100, "price": 92.5, "status": "ожидание"},
    2: {"type": "sell", "amount": 150, "price": 91.0, "status": "оплачено"},
}

@router.get("/trade/{order_id}", response_class=HTMLResponse)
async def trade_page(request: Request, order_id: int):
    if order_id not in fake_orders:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    return templates.TemplateResponse("trade.html", {"request": request, "order_id": order_id})

@router.get("/api/orders/{order_id}")
async def get_order(order_id: int):
    if order_id not in fake_orders:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    return fake_orders[order_id]

@router.post("/api/orders/{order_id}/confirm_payment")
async def confirm_payment(order_id: int):
    if order_id not in fake_orders:
        raise HTTPException(status_code=404, detail="Сделка не найдена")
    fake_orders[order_id]["status"] = "платёж отправлен"
    return {"message": "Платёж помечен как отправленный"}
