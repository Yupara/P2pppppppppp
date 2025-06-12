from fastapi import (
    FastAPI, Request, Form, UploadFile, File,
    Depends, HTTPException, status
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from uuid import uuid4
from datetime import datetime, timedelta
import os
import secrets
from passlib.context import CryptContext

# ----- Setup -----
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="CHANGE_THIS_TO_A_RANDOM_SECRET")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ----- In-memory DB -----
users = {}      # login -> {"email":..., "hashed_password":...}
ads = []
chats = {}
payments = {}
order_status = {}
blocked_until = {}
cancellations = {}
balances = {}

# ----- Auth helpers -----
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_current_user(request: Request) -> str:
    user = request.session.get("user")
    if not user or user not in users:
        raise HTTPException(status_code=401, detail="Не авторизован")
    return user

# ----- Registration/Login/Logout -----
@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@app.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...)
):
    if username in users:
        return templates.TemplateResponse("register.html", {
            "request": request, "error": "Пользователь уже существует"
        })
    if password != password2:
        return templates.TemplateResponse("register.html", {
            "request": request, "error": "Пароли не совпадают"
        })
    # Создаём пользователя
    users[username] = {
        "email": email,
        "hashed_password": get_password_hash(password)
    }
    # автоматически логиним
    request.session["user"] = username
    return RedirectResponse("/market", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    user = users.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return templates.TemplateResponse("login.html", {
            "request": request, "error": "Неверный логин или пароль"
        })
    request.session["user"] = username
    return RedirectResponse("/market", status_code=302)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)

# ----- Sample protected route -----
@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse("/market", 302)

@app.get("/market", response_class=HTMLResponse)
def market(request: Request, user: str = Depends(get_current_user)):
    balances.setdefault(user, 1000.0)
    return templates.TemplateResponse("market.html", {
        "request": request,
        "ads": ads,
        "balances": balances,
        "current_user": user
    })

# ... сюда же остальной код создания объявлений, сделок, чата, настроек, admin и т.д., 
# заменив все Depends(get_current_user) на новый get_current_user(request)

# Не забудьте везде, где был:
# def some_route(..., user: str = Depends(get_current_user))
# — сохранять сигнатуру.
