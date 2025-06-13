from sqlalchemy.orm import Session
from models import User, Ad, Order, Message

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, password: str, referral_code: str = None):
    # TODO: хеширование пароля, генерация собственного referral_code
    user = User(username=username, password=password, referral_code=referral_code)
    db.add(user); db.commit(); db.refresh(user)
    return user

def get_ads(db: Session):
    return db.query(Ad).all()

def create_ad(db: Session, ad_data):
    # TODO: заполнить created_at
    ad = Ad(**ad_data.dict())
    db.add(ad); db.commit(); db.refresh(ad)
    return ad

def create_order(db: Session, order_data, buyer_id: int):
    # TODO: логика минимальной проверки, заморозка средств
    order = Order(buyer_id=buyer_id, **order_data.dict())
    db.add(order); db.commit(); db.refresh(order)
    return order

def create_message(db: Session, order_id: int, sender_id: int, text: str):
    # TODO: timestamp
    msg = Message(order_id=order_id, sender_id=sender_id, text=text)
    db.add(msg); db.commit(); db.refresh(msg)
    return msg

# и т.д. для pay, confirm, dispute, referral, notifications...
