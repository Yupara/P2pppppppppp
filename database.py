# /app/database/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Укажите строку подключения к вашей базе данных
SQLALCHEMY_DATABASE_URL = "sqlite:///example.db"  # Пример для SQLite

# Создаём движок SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Создаём сессию
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# Функция для получения сессии базы данных (обычно используется с FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
