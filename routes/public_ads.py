from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from models import User, Ad
from database import get_db
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@router.get("/market", response_class=HTMLResponse)
def public_market(request: Request, db: Session = Depends(get_db)):
    ads = db.query(Ad).filter(Ad.is_active == True).all()
    return templates.TemplateResponse("market.html", {"request": request, "ads": ads})
