from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas, dependencies
from ..database import get_db
from typing import List

router = APIRouter(prefix="/api/orders", tags=["Orders"])

@router.get("/mine", response_model=List[schemas.OrderOut])
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_user)
):
    return db.query(models.Order).filter(models.Order.user_id == current_user.id).all()
