from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from . import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(models.User).where(models.User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: schemas.UserCreate):
    hashed = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def create_order(db: AsyncSession, order: schemas.OrderCreate, user_id: int):
    db_order = models.Order(**order.dict(), owner_id=user_id)
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)
    return db_order

async def get_orders(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.Order).offset(skip).limit(limit))
    return result.scalars().all()
