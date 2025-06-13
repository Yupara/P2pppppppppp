# app.py

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from db import engine, Base              # Ваши db.py: engine и Base
import models                            # Регистрирует модели

from auth import router as auth_router    # Ваш auth.py
from payment import router as payment_router  # Ваш payment.py

# Если вам нужны сессии — раскомментируйте оба импорта и этот блок:
# from starlette.middleware.sessions import SessionMiddleware
#
# app.add_middleware(
#     SessionMiddleware,
#     secret_key="ЗАМЕНИТЕ_НА_СЕКРЕТ"
# )

# Создание таблиц
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Статика по URL /static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Корневой маршрут — редирект на /market
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/market")

# Подключаем роутеры
app.include_router(auth_router, prefix="", tags=["auth"])
app.include_router(payment_router, prefix="", tags=["payment"])
