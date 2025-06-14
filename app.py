# app.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from db import Base, engine
import models  # чтобы SQLAlchemy "увидел" модели и создал таблицы

# СОЗДАНИЕ ВСЕХ ТАБЛИЦ (важно вызывать один раз при старте)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Подключение сессий (если используется request.session)
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

# Пример: подключение роутеров
# from routers import auth, ads
# app.include_router(auth.router)
# app.include_router(ads.router)

# Пример статики
app.mount("/static", StaticFiles(directory="static"), name="static")
