from fastapi import FastAPI, Request, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

ads_db = []
orders_db = []

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads_db})

@app.get("/create-ad", response_class=HTMLResponse)
def create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create-ad", response_class=HTMLResponse)
def create_ad(
    request: Request,
    type: str = Form(...),
    amount: float = Form(...),
    currency: str = Form(...),
    payment_method: str = Form(...),
    price: float = Form(...)
):
    ad_id = str(uuid4())
    ad = {
        "id": ad_id,
        "type": type,
        "amount": amount,
        "currency": currency,
        "payment_method": payment_method,
        "price": price,
        "seller": "demo_seller"
    }
    ads_db.append(ad)
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade(request: Request, ad_id: str):
    ad = next((a for a in ads_db if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    order_id = str(uuid4())
    order = {
        "id": order_id,
        "ad_id": ad_id,
        "status": "waiting_payment"
    }
    orders_db.append(order)
    return templates.TemplateResponse("trade.html", {"request": request, "ad": ad, "order": order})

@app.post("/trade-action/{order_id}")
def trade_action(order_id: str, action: str = Form(...)):
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if action == "paid":
        order["status"] = "paid"
    elif action == "confirmed":
        order["status"] = "confirmed"
    elif action == "dispute":
        order["status"] = "dispute"
    return RedirectResponse(f"/trade-status/{order_id}", status_code=302)

@app.get("/trade-status/{order_id}", response_class=HTMLResponse)
def trade_status(request: Request, order_id: str):
    order = next((o for o in orders_db if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return templates.TemplateResponse("trade_status.html", {"request": request, "order": order})
