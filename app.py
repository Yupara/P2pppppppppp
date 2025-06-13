from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from db import engine, Base  # <-- Base и engine из db.py
import models                # <-- здесь регистрируются все модели

from auth import router as auth_router
from payment import router as payment_router

# создаём таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="REPLACE_WITH_SECRET")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router, prefix="", tags=["auth"])
app.include_router(payment_router, prefix="", tags=["payment"])
