from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .. import schemas, crud
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=schemas.UserOut)
async def read_users_me(current_user=Depends(get_current_user)):
    return current_user

@router.get("/", response_model=List[schemas.UserOut])
async def list_users(db: AsyncSession = Depends(get_db)):
    return await crud.get_users(db)
