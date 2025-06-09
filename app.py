from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import engine, Base
from utils.auth import create_token_route, get_current_user
from routes.public_ads import router as ads_router
from routes.orders import router as orders_router
from routes.withdrawals import router as withdrawals_router
from routes.support import router as support_router
from routes.admin import router as admin_router

# Инициализация FastAPI
app = FastAPI(title="P2P Платформа")

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Монтируем статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Авторизационные маршруты: /auth/register, /auth/token, /auth/me
create_token_route(app)

# Подключаем роутеры
app.include_router(ads_router)           # /ads, /ads/my, /ads/create и т.д.
app.include_router(orders_router)        # /orders/create/{ad_id}, /orders/{id}, чат и действия
app.include_router(withdrawals_router)   # /withdrawals и связанные
app.include_router(support_router)       # /support
app.include_router(admin_router)         # /admin

# Главная страница — маркет (список публичных объявлений)
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Страница профиля пользователя
@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})
