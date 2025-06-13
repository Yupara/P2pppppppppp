from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from app import get_current_user, get_db
from models import User

router = APIRouter(prefix="/admin")

@router.get("", response_class=HTMLResponse)
def admin_dashboard(user=Depends(get_current_user), db=Depends(get_db)):
    if user.id != 1:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    # TODO: вывести споры, крупные сделки, статистику
    return "<h1>Admin</h1>"
