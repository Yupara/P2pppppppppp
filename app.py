from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from uuid import uuid4
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

ads = []

class Ad(BaseModel):
    id: str
    title: str
    price: float
    type: str  # 'buy' or 'sell'

@app.get("/", response_class=RedirectResponse)
async def root():
    return "/market"

@app.get("/market")
async def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

@app.post("/create-ad")
async def create_ad(title: str = Form(...), price: float = Form(...), type: str = Form(...)):
    new_ad = Ad(id=str(uuid4()), title=title, price=price, type=type)
    ads.append(new_ad)
    return RedirectResponse(url="/market", status_code=303)

@app.get("/trade/{ad_id}")
async def trade(request: Request, ad_id: str):
    ad = next((ad for ad in ads if ad.id == ad_id), None)
    if not ad:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    return templates.TemplateResponse("trade.html", {"request": request, "ad": ad})

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
