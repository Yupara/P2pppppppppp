from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4
from datetime import datetime, timedelta

app = FastAPI()

# Статика и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory хранилище
ads = []  # список объявлений
chats = {}  # chat per ad_id

@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse("/market", status_code=302)

@app.get("/market", response_class=HTMLResponse)
def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

@app.get("/create", response_class=HTMLResponse)
def create_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create")
def create_ad(
    request: Request,
    action: str = Form(...),
    crypto: str = Form(...),
    fiat: str = Form(...),
    rate: float = Form(...),
    min_amount: float = Form(...),
    max_amount: float = Form(...),
    payment_method: str = Form(...),
    comment: str = Form("")
):
    ad_id = str(uuid4())
    ad = {
        "id": ad_id,
        "action": action,
        "crypto": crypto,
        "fiat": fiat,
        "rate": rate,
        "min_amount": min_amount,
        "max_amount": max_amount,
        "payment_method": payment_method,
        "comment": comment,
        "user": "Павел",
        "rating": 99,
        "completed": 55
    }
    ads.append(ad)
    chats[ad_id] = []
    return RedirectResponse("/market", status_code=302)

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade_page(request: Request, ad_id: str):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    # Таймер 15 мин
    end_time = datetime.utcnow() + timedelta(minutes=15)
    remaining = int((end_time - datetime.utcnow()).total_seconds())
    return templates.TemplateResponse("trade.html", {
        "request": request, "ad": ad, "remaining": remaining, "messages": chats[ad_id]
    })

@app.post("/trade/{ad_id}/message")
def post_message(ad_id: str, message: str = Form(...)):
    if ad_id in chats:
        chats[ad_id].append({"user": "Вы", "text": message})
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/paid")
def mark_paid(ad_id: str):
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/confirm")
def mark_confirm(ad_id: str):
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)

@app.post("/trade/{ad_id}/dispute")
def mark_dispute(ad_id: str):
    return RedirectResponse(f"/trade/{ad_id}", status_code=302)
