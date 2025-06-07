from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routes import auth, orders

# Создание таблиц
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="P2P Платформа",
    description="Простая P2P-платформа с авторизацией и сделками",
    version="1.0.0"
)

# CORS (для фронтенда)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или ['http://localhost:8000'] и т.п.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])


@app.get("/")
def root():
    return {"message": "P2P API работает"}
