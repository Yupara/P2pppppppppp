from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, orders
from db import Base, engine

# Создаем таблицы в базе данных (если еще не созданы)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="P2P Crypto Exchange",
    description="P2P платформа как у Bybit",
    version="1.0.0"
)

# CORS для разрешения запросов от frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # поставь frontend адрес вместо "*" если нужно
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем маршруты
app.include_router(auth.router)
app.include_router(orders.router)

@app.get("/")
def root():
    return {"message": "Добро пожаловать в P2P API"}
