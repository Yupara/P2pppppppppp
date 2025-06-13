from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import crud
from app import get_db, get_current_user

router = APIRouter()

@router.post("/referral/use")
def use_referral(code: str, db: Session = Depends(get_db),
                 user=Depends(get_current_user)):
    # TODO: найти по code, начислить бонус, увеличить referrals_count
    return {"ok": True}
