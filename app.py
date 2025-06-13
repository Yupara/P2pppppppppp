from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from db import engine, Base
import models

from auth import router as auth_router
from payment import router as payment_router
from settings import router as settings_router
from orders import router as orders_router
from support import router as support_router
from verify import router as verify_router
from admin import router as admin_router

import tasks

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/market")

app.include_router(auth_router,     tags=["auth"])
app.include_router(payment_router,  tags=["payment"])
app.include_router(settings_router, tags=["settings"])
app.include_router(orders_router,   tags=["orders"])
app.include_router(support_router,  tags=["support"])
app.include_router(verify_router,   tags=["verify"])
app.include_router(admin_router,    tags=["admin"])

tasks.start_scheduler()

import tasks
tasks.start_scheduler()
