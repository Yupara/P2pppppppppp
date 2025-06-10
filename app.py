from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from uuid import uuid4
import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class Ad:
    def __init__(self, id, type, price, currency, method):
        self.id = id
        self.type = type
        self.price = price
        self.currency = currency
        self.method = method

ads_db = []
chats = {}  # chat_id: [messages]

@app.get("/", response_class=HTMLResponse)
def read_market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads_db})

@app.post("/ads/create")
def create_ad(
    request: Request,
    type: str = Form(...),
    price: float = Form(...),
    currency: str = Form(...),
    method: str = Form(...)
):
    ad = Ad(
        id=str(uuid4()),
        type=type,
        price=price,
        currency=currency,
        method=method
    )
    ads_db.append(ad)
    return RedirectResponse("/", status_code=302)

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def open_trade(request: Request, ad_id: str):
    ad = next((a for a in ads_db if a.id == ad_id), None)
    if not ad:
        return HTMLResponse(content="Ad not found", status_code=404)
    
    trade_id = str(uuid4())
    chats[trade_id] = []
    end_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    return templates.TemplateResponse("trade.html", {
        "request": request,
        "ad": ad,
        "trade_id": trade_id,
        "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.post("/chat/send")
def send_message(request: Request, trade_id: str = Form(...), message: str = Form(...)):
    if trade_id in chats:
        chats[trade_id].append(message)
    return RedirectResponse(f"/trade/{trade_id}", status_code=302)
