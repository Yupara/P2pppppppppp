from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .. import schemas, crud
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=schemas.OrderOut)
async def create_order(order: schemas.OrderCreate, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await crud.create_order(db, order, user_id=current_user.id)

@router.get("/", response_model=List[schemas.OrderOut])
async def list_orders(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.get_orders(db, skip, limit)
