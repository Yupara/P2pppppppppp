from fastapi import FastAPI, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List
from uuid import uuid4
import uvicorn

app = FastAPI()

def create_test_data():
    db = SessionLocal()

    existing_user = db.query(User).filter_by(username="seller123").first()
    if existing_user:
        db.close()
        return

    seller = User(username="seller123", hashed_password="123456")  # временно без хэша
    db.add(seller)
    db.commit()
    db.refresh(seller)

    ad = Ad(
        user_id=seller.id,
        ad_type="sell",
        amount=100,
        price=1.0,
        currency="USDT",
        payment_method="Bank",
        description="Test USDT sale"
    )
    db.add(ad)
    db.commit()
    db.close()

# Добавь ВЫЗОВ функции сразу после её описания:
create_test_data()

# Далее как обычно:
@app.get("/")
def home():
    return {"message": "Hello World"}
