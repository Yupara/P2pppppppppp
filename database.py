from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Здесь укажи путь к своей БД, например SQLite или PostgreSQL
DATABASE_URL = "sqlite:///./p2p.db"
# Для PostgreSQL: 
# DATABASE_URL = "postgresql://user:password@localhost:5432/mydatabase"

# Создаём движок
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  # Для SQLite
)

# Базовый класс моделей
Base = declarative_base()

# Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Зависимость для получения сессии в маршрутах
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
