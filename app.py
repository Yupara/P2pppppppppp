# app.py
from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

ads = []  # список объявлений
payments = {}  # хранит информацию о сделках
chats = {}  # чаты сделок
order_status = {}  # статус сделки
receipts = {}  # подтверждённые сделки

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

@app.get("/create", response_class=HTMLResponse)
def create_ad_form(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})

@app.post("/create")
def create_ad(
    title: str = Form(...),
    price: float = Form(...),
    amount: float = Form(...),
    payment_method: str = Form(...),
    min_limit: float = Form(...),
    max_limit: float = Form(...),
    condition: str = Form(...),
):
    ad_id = str(uuid4())
    ads.append({
        "id": ad_id,
        "title": title,
        "price": price,
        "amount": amount,
        "payment_method": payment_method,
        "min_limit": min_limit,
        "max_limit": max_limit,
        "condition": condition,
        "owner": "Павел",
        "completed_orders": 55,
        "rating": 99
    })
    return RedirectResponse("/", status_code=302)

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade_view(request: Request, ad_id: str):
    ad = next((x for x in ads if x["id"] == ad_id), None)
    if not ad:
        return HTMLResponse("Объявление не найдено", status_code=404)
    status = order_status.get(ad_id, "pending")
    messages = chats.get(ad_id, [])
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "order_status": order_status,
        "messages": messages
    })

@app.post("/trade/{ad_id}/buy")
def trade_buy(ad_id: str, amount: float = Form(...)):
    payments[ad_id] = {
        "amount": amount,
        "paid": False
    }
    order_status[ad_id] = "pending"
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/pay")
def trade_pay(ad_id: str,
    card_number: str = Form(...),
    exp_date: str = Form(...),
    cvv: str = Form(...),
):
    payments[ad_id]["paid"] = True
    order_status[ad_id] = "paid"
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/confirm_receipt")
def trade_confirm_receipt(ad_id: str):
    if order_status.get(ad_id) == "paid":
        order_status[ad_id] = "released"
        receipts[ad_id] = True
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/cancel")
def trade_cancel(ad_id: str):
    if order_status.get(ad_id) in ["pending", "disputed"]:
        order_status[ad_id] = "cancelled"
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/dispute")
def trade_dispute(ad_id: str):
    if order_status.get(ad_id) == "paid":
        order_status[ad_id] = "disputed"
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/message")
async def trade_message(ad_id: str, message: str = Form(None), image: UploadFile = File(None)):
    entry = {"user": "Вы", "text": message}
    if image:
        os.makedirs("static/uploads", exist_ok=True)
        path = f"static/uploads/{uuid4().hex}_{image.filename}"
        with open(path, "wb") as f:
            f.write(await image.read())
        entry["image_url"] = path.replace("static", "/static")
    chats.setdefault(ad_id, []).append(entry)
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)
