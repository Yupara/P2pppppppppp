from fastapi import FastAPI, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from auth import get_current_user
from database import Base, engine, SessionLocal
from models import User, Ad, Order
from uuid import uuid4

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def home(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("home.html", {"request": request, "user": user})


@app.get("/market", response_class=HTMLResponse)
def market(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ads = db.query(Ad).filter(Ad.owner_id != user.id).all()
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads, "user": user})


@app.get("/ads/create", response_class=HTMLResponse)
def create_ad_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("create_ad.html", {"request": request, "user": user})


@app.post("/ads/create", response_class=HTMLResponse)
def create_ad(
    request: Request,
    crypto: str = Form(...),
    fiat: str = Form(...),
    rate: float = Form(...),
    min_limit: float = Form(...),
    max_limit: float = Form(...),
    payment_method: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ad = Ad(
        crypto=crypto,
        fiat=fiat,
        rate=rate,
        min_limit=min_limit,
        max_limit=max_limit,
        payment_method=payment_method,
        owner_id=user.id,
    )
    db.add(ad)
    db.commit()
    db.refresh(ad)
    return RedirectResponse("/market", status_code=302)


@app.get("/trade/{order_id}", response_class=HTMLResponse)
def trade_page(order_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    return templates.TemplateResponse("trade.html", {"request": request, "order": order, "user": user})


@app.post("/orders/create/{ad_id}", response_class=HTMLResponse)
def create_order(
    request: Request,
    ad_id: int,
    amount: float = Form(...),
    payment: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        return templates.TemplateResponse("error.html", {"request": request, "msg": "Объявление не найдено"})

    if ad.owner_id == user.id:
        return templates.TemplateResponse("error.html", {"request": request, "msg": "Нельзя создать сделку с самим собой"})

    order = Order(
        ad_id=ad.id,
        buyer_id=user.id,
        seller_id=ad.owner_id,
        amount=amount,
        payment_method=payment,
        status="pending",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return RedirectResponse(f"/trade/{order.id}", status_code=302)
