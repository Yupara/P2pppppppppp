# app.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from db import engine, Base          # <-- из db.py
import models                        # <-- создаёт таблицы через Base.metadata
from auth import router as auth_router
from payment import router as pay_router
# ... другие роутеры ...

# Создать все таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="CHANGE_THIS_SECRET")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем маршруты
app.include_router(auth_router, prefix="", tags=["auth"])
app.include_router(pay_router, prefix="", tags=["payment"])
# ... остальные роутеры ...
