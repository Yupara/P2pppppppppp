from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models
from auth import router as auth_router
from payment import router as pay_router
from referral import router as ref_router
from notifications import *
from bot import router as bot_router
from admin import router as admin_router

# DB
DATABASE_URL = "sqlite:///./p2p.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
models.Base.metadata.create_all(bind=engine)

# App
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="CHANGE_THIS_SECRET")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers
app.include_router(auth_router, prefix="", tags=["auth"])
app.include_router(pay_router, prefix="", tags=["payment"])
app.include_router(ref_router, prefix="", tags=["referral"])
app.include_router(bot_router, prefix="/bot", tags=["bot"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
