from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import engine, Base, get_db
from utils.auth import create_token_route, oauth2_scheme, get_current_user
from routes.orders import router as orders_router
from routes.public_ads import router as ads_router
# Импорт моделей, чтобы таблицы создались
import models

# Инициализация FastAPI
app = FastAPI(title="P2P Pлатформа")

# Создание таблиц в БД
Base.metadata.create_all(bind=engine)

# Статика и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Настройка роутов аутентификации
create_token_route(app)

# Подключение маршрутов
app.include_router(ads_router, prefix="", tags=["Public Ads"])
app.include_router(orders_router, prefix="", tags=["Orders"])

# Маршрут главной страницы (публичный маркет)
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("market.html", {"request": request})

# Маршрут профиля
@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("templates/profile.html", {"request": request})

# При необходимости добавьте другие страницы (каталог, админка и т.д.) ниже

# models.py
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_verified = Column(Boolean, default=False)  # ✅ Новое поле
