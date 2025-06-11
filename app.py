# app.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import time, random

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")   # serve static files
templates = Jinja2Templates(directory="templates")

# In-memory storage
ads = []
trades = []
ad_counter = 1
trade_counter = 1

@app.get("/create_ad", response_class=HTMLResponse)
async def get_create_ad(request: Request):
    # Show the ad creation form
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create_ad")
async def create_ad(ad_type: str = Form(...), amount: float = Form(...), 
                    price: float = Form(...), payment: str = Form(...)):
    # Handle ad submission and store it in memory
    global ad_counter
    ad = {"id": ad_counter, "type": ad_type, "amount": amount, "price": price, "payment": payment}
    ad_counter += 1
    ads.append(ad)
    # After creating the ad, redirect to the market page
    return RedirectResponse(url="/market", status_code=303)

@app.get("/market", response_class=HTMLResponse)
async def market(request: Request):
    # Display all ads
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

@app.get("/trade/new")
async def new_trade(ad_id: int):
    # Create a new trade for the given ad_id and redirect to trade page
    global trade_counter
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if ad is None:
        return RedirectResponse(url="/market")
    # Initialize the trade object
    trade = {
        "id": trade_counter,
        "ad": ad,
        "is_paid": False,
        "is_confirmed": False,
        "is_dispute": False,
        "messages": [],
        "start": time.time(),
        "expires": time.time() + random.randint(15, 30)*60  # timer 15-30 min
    }
    trade_counter += 1
    trades.append(trade)
    # Redirect to the trade detail page
    return RedirectResponse(url=f"/trade/{trade['id']}", status_code=303)

@app.get("/trade/{trade_id}", response_class=HTMLResponse)
async def get_trade(request: Request, trade_id: int):
    # Show trade page with details and chat
    trade = next((t for t in trades if t["id"] == trade_id), None)
    if trade is None:
        return RedirectResponse(url="/market")
    # Calculate remaining time (in seconds)
    remaining = int(trade["expires"] - time.time())
    if remaining < 0:
        remaining = 0
    return templates.TemplateResponse("trade.html", {
        "request": request, "trade": trade, "remaining": remaining
    })

@app.post("/trade/{trade_id}/paid")
async def trade_paid(trade_id: int):
    # Mark "paid" status
    trade = next((t for t in trades if t["id"] == trade_id), None)
    if trade:
        trade["is_paid"] = True
    return RedirectResponse(url=f"/trade/{trade_id}", status_code=303)

@app.post("/trade/{trade_id}/confirm")
async def trade_confirm(trade_id: int):
    # Mark "confirmed receipt"
    trade = next((t for t in trades if t["id"] == trade_id), None)
    if trade:
        trade["is_confirmed"] = True
    return RedirectResponse(url=f"/trade/{trade_id}", status_code=303)

@app.post("/trade/{trade_id}/dispute")
async def trade_dispute(trade_id: int):
    # Mark "dispute opened"
    trade = next((t for t in trades if t["id"] == trade_id), None)
    if trade:
        trade["is_dispute"] = True
    return RedirectResponse(url=f"/trade/{trade_id}", status_code=303)

@app.post("/trade/{trade_id}/chat")
async def trade_chat(trade_id: int, message: str = Form(...)):
    # Add a message to the trade chat history
    trade = next((t for t in trades if t["id"] == trade_id), None)
    if trade:
        trade["messages"].append(message)
    return RedirectResponse(url=f"/trade/{trade_id}", status_code=303)
