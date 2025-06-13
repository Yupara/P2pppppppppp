# app.py

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from db import engine, Base
import models

from auth import router as auth_router
from payment import router as payment_router
from settings import router as settings_router
from orders import router as orders_router
from support import router as support_router
from verify import router as verify_router
from admin import router as admin_router

import tasks  # фоновые задачи (APS cheduler)

# создаём все таблицы (если ещё нет)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# если нужны сессии — раскомментируйте:
# from starlette.middleware.sessions import SessionMiddleware
# app.add_middleware(SessionMiddleware, secret_key="ВАШ_СЕКРЕТ")

# статика под /static
app.mount("/static", StaticFiles(directory="static"), name="static")

# корень → /market
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/market")

# подключаем все роутеры
app.include_router(auth_router,     prefix="", tags=["auth"])
app.include_router(payment_router,  prefix="", tags=["payment"])
app.include_router(settings_router, prefix="", tags=["settings"])
app.include_router(orders_router,   prefix="", tags=["orders"])
app.include_router(support_router,  prefix="", tags=["support"])
app.include_router(verify_router,   prefix="", tags=["verify"])
app.include_router(admin_router,    prefix="", tags=["admin"])

# запускаем фоновые задачи (ежедневный отчёт, крупные сделки)
tasks.start_scheduler()
