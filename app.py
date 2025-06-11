from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from database import Base, engine
from auth import router as auth_router
from users import router as users_router
from ads import router as ads_router
from orders import router as orders_router

app = FastAPI()

# Подключение шаблонов и статики
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Подключение CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(ads_router, prefix="/ads", tags=["ads"])
app.include_router(orders_router, prefix="/orders", tags=["orders"])
