from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uuid import uuid4

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

ads = []

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/market", response_class=HTMLResponse)
def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

@app.get("/create", response_class=HTMLResponse)
def create_ad(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create", response_class=HTMLResponse)
def create_ad_post(request: Request, type: str = Form(...), amount: float = Form(...), payment: str = Form(...)):
    ad_id = str(uuid4())
    ads.append({"id": ad_id, "type": type, "amount": amount, "payment": payment})
    return RedirectResponse("/market", status_code=302)

@app.get("/trade/{ad_id}", response_class=HTMLResponse)
def trade(request: Request, ad_id: str):
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        return HTMLResponse(content="Объявление не найдено", status_code=404)
    return templates.TemplateResponse("trade.html", {"request": request, "ad": ad})
