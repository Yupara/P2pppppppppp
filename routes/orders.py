from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from schemas.order import OrderCreate, OrderOut
from models import Order, User
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from utils.auth import SECRET_KEY, ALGORITHM

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Неверный токен")
    user = db.query(User).get(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user

@router.post("/orders", response_model=OrderOut)
def create_order(order: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_order = Order(**order.dict(), owner_id=current_user.id)
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

@router.get("/orders/mine", response_model=list[OrderOut])
def get_my_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Order).filter(Order.owner_id == current_user.id).all()
