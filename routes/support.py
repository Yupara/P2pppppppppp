from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from utils.auth import get_current_user
from utils.telegram import notify_admin

router = APIRouter()

class SupportRequest(BaseModel):
    message: str

@router.post("/support")
def support(req: SupportRequest, current_user=Depends(get_current_user)):
    notify_admin(f"💬 <b>Новый запрос поддержки</b>\nПользователь: {current_user.username}\n\n{req.message}")
    return {"detail": "Запрос отправлен"}
