from fastapi import FastAPI
from .database import engine, Base
from .routers import auth, users, orders

app = FastAPI(title="P2P Exchange")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(orders.router)
