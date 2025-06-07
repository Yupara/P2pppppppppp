from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import Base, engine
from routes import auth, orders, chat
import uvicorn

# Инициализация базы данных
Base.metadata.create_all(bind=engine)

# Приложение FastAPI
app = FastAPI(title="P2P Platform", version="1.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Можно ограничить до фронта
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(chat.router)

# Отдача статики (HTML, JS, CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Корневая страница (например, index.html)
@app.get("/")
def root():
    return {"message": "Добро пожаловать в P2P платформу!"}

# Запуск сервера локально
# if __name__ == "__main__":
#     uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
