from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from uuid import uuid4

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class User:
    def __init__(self, username):
        self.username = username

class Ad:
    def __init__(self, id, type, price, currency, method, user):
        self.id = id
        self.type = type
        self.price = price
        self.currency = currency
        self.method = method
        self.user = user

ads_db = []
test_user = User("demo")

def get_current_user(request: Request):
    return test_user  # Заглушка, возвращает одного юзера

@app.get("/market", response_class=HTMLResponse)
def market(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads_db})

@app.post("/ads/create")
def create_ad(request: Request, type: str = Form(...), price: float = Form(...), currency: str = Form(...), method: str = Form(...)):
    user = get_current_user(request)
    ad = Ad(id=str(uuid4()), type=type, price=price, currency=currency, method=method, user=user)
    ads_db.append(ad)
    return RedirectResponse("/market", status_code=302)
