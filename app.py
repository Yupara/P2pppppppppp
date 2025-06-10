from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from uuid import uuid4
from typing import List, Dict
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class Ad(BaseModel):
    id: str
    username: str
    type: str  # buy or sell
    amount: float
    currency: str
    payment: str

class Order(BaseModel):
    id: str
    ad_id: str
    buyer: str
    seller: str
    status: str  # created, paid, confirmed, disputed

ads: List[Dict] = []
orders: List[Dict] = []
messages: Dict[str, List[Dict[str, str]]] = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

@app.post("/create_ad")
async def create_ad(
    username: str = Form(...),
    type: str = Form(...),
    amount: float = Form(...),
    currency: str = Form(...),
    payment: str = Form(...)
):
    ad = Ad(
        id=str(uuid4()),
        username=username,
        type=type,
        amount=amount,
        currency=currency,
        payment=payment
    )
    ads.append(ad.dict())
    return RedirectResponse("/", status_code=302)

@app.post("/buy/{ad_id}")
async def buy_ad(ad_id: str):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    buyer = "buyer123"
    order = Order(
        id=str(uuid4()),
        ad_id=ad_id,
        buyer=buyer,
        seller=ad["username"],
        status="created"
    )
    orders.append(order.dict())
    return RedirectResponse(url=f"/trade/{ad_id}", status_code=302)

def get_order_by_ad(ad_id):
    return next((o for o in orders if o["ad_id"] == ad_id), None)

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
async def trade_page(request: Request, ad_id: str):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    msg_list = messages.get(ad_id, [])
    order = get_order_by_ad(ad_id)
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "messages": msg_list,
        "order": order or {"status": "created"}
    })

@app.post("/send_message/{ad_id}")
async def send_message(ad_id: str, username: str = Form(...), message: str = Form(...)):
    messages.setdefault(ad_id, []).append({"username": username, "message": message})
    return RedirectResponse(url=f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/pay")
async def mark_paid(ad_id: str):
    order = get_order_by_ad(ad_id)
    if order:
        order["status"] = "paid"
    return RedirectResponse(url=f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/confirm")
async def mark_confirmed(ad_id: str):
    order = get_order_by_ad(ad_id)
    if order:
        order["status"] = "confirmed"
    return RedirectResponse(url=f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/dispute")
async def mark_disputed(ad_id: str):
    order = get_order_by_ad(ad_id)
    if order:
        order["status"] = "disputed"
    return RedirectResponse(url=f"/trade/{ad_id}", status_code=302)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
