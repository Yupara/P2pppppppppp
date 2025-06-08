from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from routes import auth, ads, orders

app = FastAPI(title="P2P Платформа")

# Подключаем статику и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CORS (если frontend на другом домене)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # для разработки можно *, в проде — только нужные
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Корневая страница — редирект на объявления
@app.get("/")
async def root():
    return RedirectResponse("/ads")

# Роуты
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(ads.router, prefix="/ads", tags=["ads"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
