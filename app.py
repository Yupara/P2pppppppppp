# app.py

import os
from datetime import datetime
from fastapi import (
    FastAPI, Request, Form,
    Depends, HTTPException
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy import (
    create_engine, Column,
    Integer, String, Float,
    ForeignKey, DateTime, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# --- База ---
DATABASE_URL = "sqlite:///./p2p.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Модели ---
class Ad(Base):
    __tablename__ = "ads"
    id              = Column(Integer, primary_key=True, index=True)
    type            = Column(String, nullable=False)
    crypto          = Column(String, nullable=False)
    fiat            = Column(String, nullable=False)
    amount          = Column(Float, nullable=False)
    price           = Column(Float, nullable=False)
    min_limit       = Column(Float, nullable=False)
    max_limit       = Column(Float, nullable=False)
    payment_methods = Column(String, nullable=False)

# создаём таблицы
Base.metadata.create_all(bind=engine)

# --- FastAPI ---
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Маршруты ---

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/market")

@app.get("/market", response_class=HTMLResponse)
def market(request: Request, db: Session = Depends(get_db)):
    ads = db.query(Ad).all()
    return templates.TemplateResponse("market.html", {
        "request": request,
        "ads": ads
    })

@app.get("/create_ad", response_class=HTMLResponse)
def create_ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@app.post("/create_ad")
def create_ad(
    request: Request,
    type: str = Form(...),
    crypto: str = Form(...),
    fiat: str = Form(...),
    amount: float = Form(...),
    price: float = Form(...),
    min_limit: float = Form(...),
    max_limit: float = Form(...),
    payment_methods: str = Form(...),
    db: Session = Depends(get_db)
):
    ad = Ad(
        type=type,
        crypto=crypto,
        fiat=fiat,
        amount=amount,
        price=price,
        min_limit=min_limit,
        max_limit=max_limit,
        payment_methods=payment_methods
    )
    db.add(ad)
    db.commit()
    return RedirectResponse("/market", status_code=302)
