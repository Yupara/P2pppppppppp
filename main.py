from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import pytz

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Database setup
engine = create_engine('sqlite:///p2p_exchange.db', echo=True)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    orders_completed = Column(Integer, default=0)
    last_seen = Column(DateTime, default=datetime.utcnow)
    rating = Column(Float, default=99.0)
    completion_rate = Column(Float, default=100.0)
    avg_transfer_time = Column(String, default="2 мин.")
    offers = relationship("Offer", back_populates="user")

@app.get("/")
async def read_root():
    return {"message": "Server is running"}

# (остальной код, включая маршруты и модели)
