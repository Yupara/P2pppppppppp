# app.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

import models           # ваши модели из models.py
from db import engine, Base  # подключаем движок и Base
from auth import router as auth_router
from payment import router as pay_router
from referral import router as ref_router
from bot import router as bot_router
from admin import router as admin_router

# Создаём таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="CHANGE_THIS_SECRET")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router)
app.include_router(pay_router)
app.include_router(ref_router)
app.include_router(bot_router, prefix="/bot")
app.include_router(admin_router, prefix="/admin")
