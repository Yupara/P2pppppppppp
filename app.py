# app.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import RedirectResponse

# Импорт ваших роутеров
from auth import router as auth_router
from payment import router as payment_router
from settings import router as settings_router
from orders import router as orders_router
from support import router as support_router
from verify import router as verify_router
from admin import router as admin_router

import tasks  # APScheduler

app = FastAPI()

# 1) Мидлвар для сессий — обязательно до любых маршрутов, где читается request.session
app.add_middleware(
    SessionMiddleware,
    secret_key="ВАШ_СЕКРЕТ_КЛЮЧ_ЗДЕСЬ"  # замените на свой случайный ключ
)

# 2) Статика (favicon, стили и т.д.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 3) Редирект корня на /market
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/market")

# 4) Подключаем роутеры
app.include_router(auth_router,     tags=["auth"])
app.include_router(payment_router,  prefix="", tags=["payment"])
app.include_router(settings_router, prefix="", tags=["settings"])
app.include_router(orders_router,   prefix="", tags=["orders"])
app.include_router(support_router,  prefix="", tags=["support"])
app.include_router(verify_router,   prefix="", tags=["verify"])
app.include_router(admin_router,    prefix="", tags=["admin"])

# 5) Запускаем фоновые задачи (ежедневный отчёт, проверки сделок)
tasks.start_scheduler()
