from models import User, Ad  # Импортируй свои модели
from database import SessionLocal  # Или как у тебя называется сессия

def create_test_data():
    db = SessionLocal()

    # Проверка: если пользователь уже есть — пропускаем
    existing_user = db.query(User).filter_by(username="seller123").first()
    if existing_user:
        db.close()
        return

    # Создаем пользователя-продавца
    seller = User(username="seller123", hashed_password="123456")  # если bcrypt, то захешируй
    db.add(seller)
    db.commit()
    db.refresh(seller)

    # Создаем объявление
    ad = Ad(
        user_id=seller.id,
        ad_type="sell",
        amount=100,
        price=1.0,
        currency="USDT",
        payment_method="Bank",
        description="Test USDT sale"
    )
    db.add(ad)
    db.commit()
    db.close()

# Вызови функцию при запуске (только один раз!)
create_test_data()
