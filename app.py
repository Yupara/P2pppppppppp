from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uuid

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

ads = []
messages = {}

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

@app.post("/create-ad")
def create_ad(title: str = Form(...), price: float = Form(...), type: str = Form(...)):
    ad = {
        "id": str(uuid.uuid4()),
        "title": title,
        "price": price,
        "type": type
    }
    ads.append(ad)
    return RedirectResponse("/", status_code=303)

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade_page(request: Request, ad_id: str):
    ad = next((ad for ad in ads if ad["id"] == ad_id), None)
    if not ad:
        return HTMLResponse("Объявление не найдено", status_code=404)
    return templates.TemplateResponse("trade.html", {"request": request, "ad": ad, "messages": messages.get(ad_id, [])})

@app.post("/trade/{ad_id}/message")
def post_message(ad_id: str, sender: str = Form(...), text: str = Form(...)):
    if ad_id not in messages:
        messages[ad_id] = []
    messages[ad_id].append({"sender": sender, "text": text})
    return RedirectResponse(f"/trade/{ad_id}", status_code=303)

@app.post("/trade/{ad_id}/action")
def handle_action(ad_id: str, action: str = Form(...)):
    return RedirectResponse(f"/trade/{ad_id}", status_code=303)
