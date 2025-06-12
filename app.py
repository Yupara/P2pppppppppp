from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="ВАШ_СЕКРЕТ_ДЛЯ_СЕССИЙ")
templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Простая in-memory «база» пользователей
users = {}  # username -> {"email":..., "hashed_password":...}

def hash_password(pw: str) -> str:
    return pwd_context.hash(pw)

def verify_password(pw: str, hashed: str) -> bool:
    return pwd_context.verify(pw, hashed)

# Получение текущего пользователя из сессии
def get_current_user(request: Request) -> str:
    user = request.session.get("user")
    if not user or user not in users:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован")
    return user

@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@app.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...)
):
    if username in users:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Пользователь уже существует"})
    if password != password2:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Пароли не совпадают"})
    users[username] = {
        "email": email,
        "hashed_password": hash_password(password)
    }
    request.session["user"] = username
    return RedirectResponse("/market", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    u = users.get(username)
    if not u or not verify_password(password, u["hashed_password"]):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин или пароль"})
    request.session["user"] = username
    return RedirectResponse("/market", status_code=302)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)
