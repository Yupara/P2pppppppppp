from fastapi import FastAPI, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from database import Base, engine, SessionLocal
from models import User, Ad, Order, Message
from auth import get_current_user
import uvicorn

app = FastAPI()

# Статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Зависимость для сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Главная страница — рынок
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    ads = db.query(Ad).all()
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})

# Страница авторизованного пользователя
@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})

# Пример обработки формы (отправка сообщения в сделке)
@app.post("/orders/{order_id}/message")
def send_message(order_id: int, request: Request, text: str = Form(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    message = Message(order_id=order_id, sender_id=user.id, content=text)
    db.add(message)
    db.commit()
    return RedirectResponse(url=f"/orders/{order_id}", status_code=303)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
