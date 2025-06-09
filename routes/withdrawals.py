from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.status import HTTP_302_FOUND

from database import get_db
from models import Withdrawal, User
from utils.auth import get_current_user

router = APIRouter(prefix="/withdrawals", tags=["withdrawals"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def withdrawals_page(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Показываем историю заявок пользователя
    items = db.query(Withdrawal).filter(Withdrawal.user_id == user.id).order_by(Withdrawal.created_at.desc()).all()
    return templates.TemplateResponse("withdrawals.html", {
        "request": request,
        "withdrawals": items,
        "balance": user.referral_earnings + user.commission_balance  # или где вы храните общий баланс
    })

@router.post("/create")
def create_withdrawal(amount: float = Form(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    total_balance = user.referral_earnings + user.commission_balance
    if amount <= 0 or amount > total_balance:
        raise HTTPException(400, "Неверная сумма вывода")
    # Создаём заявку
    w = Withdrawal(user_id=user.id, amount=amount)
    db.add(w)
    # Уменьшаем баланс сразу
    user.referral_earnings -= min(user.referral_earnings, amount)
    remaining = amount - min(user.referral_earnings + min(0, amount))
    user.commission_balance -= max(0, remaining)
    db.commit()
    return RedirectResponse(url="/withdrawals", status_code=HTTP_302_FOUND)

@router.post("/{w_id}/cancel")
def cancel_withdrawal(w_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    w = db.query(Withdrawal).filter(Withdrawal.id == w_id, Withdrawal.user_id == user.id).first()
    if not w or w.status != WithdrawalStatus.pending:
        raise HTTPException(400, "Невозможно отменить")
    # возвращаем сумму на баланс
    user.referral_earnings += w.amount  # или распределяете по очереди
    w.status = WithdrawalStatus.canceled
    db.commit()
    return RedirectResponse(url="/withdrawals", status_code=HTTP_302_FOUND)
