from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models import User
from utils.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/verify/{user_id}")
def verify_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Нет доступа")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user.is_verified = True
    db.commit()
    return {"detail": f"Пользователь {user.username} верифицирован"}
