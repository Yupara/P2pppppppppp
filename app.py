# app.py

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from db import engine, Base
import models

from auth import router as auth_router
from payment import router as payment_router

# Создаём таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    # если у вас нужны сессии
    # from starlette.middleware.sessions import SessionMiddleware
    # app.add_middleware(SessionMiddleware, secret_key="YOUR_SECRET")
)

# Статика
app.mount("/static", StaticFiles(directory="static"), name="static")

# Корневой маршрут — Перенаправляет на /market
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/market")

# Подключаем роутеры
app.include_router(auth_router)
app.include_router(payment_router)
