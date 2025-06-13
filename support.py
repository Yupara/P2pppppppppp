# support.py

import os
import openai
from fastapi import (
    APIRouter, Request, Depends, Form, HTTPException
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from db import get_db
from auth import get_current_user
import models

openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/support", response_class=HTMLResponse)
def support_page(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    # Загрузить последние 20 сообщений чата из БД, если нужно
    return templates.TemplateResponse("support.html", {
        "request": request,
        "user": user,
        "messages": []  # пока пусто
    })


@router.post("/support/message")
def support_message(
    request: Request,
    text: str = Form(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    # Эскалация на оператора
    if "оператор" in text.lower():
        # здесь вместо бота — уведомление админа, например, логируем
        # можно отправить email/SMS оператору
        raise HTTPException(
            status_code=200,
            detail="Запрос передан оператору, вы скоро получите ответ."
        )

    # Генерируем ответ ботом
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content": text}]
        )
        bot_reply = resp.choices[0].message.content
    except Exception as e:
        bot_reply = "Извините, бот сейчас недоступен."

    # (опционально) сохранить в БД историю сообщений

    # После обработки — рендерим страницу снова или делаем редирект
    return templates.TemplateResponse("support.html", {
        "request": request,
        "user": user,
        "messages": [
            {"sender": user.username, "text": text},
            {"sender": "Бот поддержки", "text": bot_reply}
        ]
    })
