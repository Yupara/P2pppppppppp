from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from db import engine, Base     # движок и декларативный Base
import models                   # регистрирует все модели

from auth import router as auth_router
from payment import router as payment_router
from settings import router as settings_router  # новый роутер

# создание таблиц
Base.metadata.create_all(bind=engine)

app = FastAPI()

# сессии (раскомментируйте при необходимости)
# from starlette.middleware.sessions import SessionMiddleware
# app.add_middleware(SessionMiddleware, secret_key="ВАШ_СЕКРЕТ")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/market")

app.include_router(auth_router, prefix="", tags=["auth"])
app.include_router(payment_router, prefix="", tags=["payment"])
app.include_router(settings_router, prefix="", tags=["settings"])
