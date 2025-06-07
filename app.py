from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, orders, chat
from database import Base, engine

# Создание таблиц в БД (если ещё не созданы)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="P2P Crypto Exchange",
    version="1.0.0"
)

# Разрешаем CORS (если фронтенд на другом домене)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Укажи домен фронтенда для безопасности
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение маршрутов
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(orders.router, prefix="/api", tags=["orders"])
app.include_router(chat.router, prefix="/api", tags=["chat"])

@app.get("/")
def root():
    return {"message": "P2P API работает"}
