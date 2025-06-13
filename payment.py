from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
import crud, schemas
from app import get_db, get_current_user

router = APIRouter()

@router.get("/create_ad", response_class=HTMLResponse)
def ad_form(request: Request):
    return templates.TemplateResponse("create_ad.html", {"request": request})

@router.post("/create_ad")
def ad_create(request: Request, form: schemas.AdCreate = Depends(schemas.AdCreate),
              db: Session = Depends(get_db), user=Depends(get_current_user)):
    ad = crud.create_ad(db, form, user.id)
    return RedirectResponse("/market", status_code=302)

@router.get("/create_order/{ad_id}")
def order_create(ad_id: int, request: Request,
                 db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = crud.create_order(db, schemas.OrderCreate(ad_id=ad_id, amount=...),
                              user.id)
    return RedirectResponse(f"/trade/{order.id}", status_code=302)

@router.get("/trade/{order_id}", response_class=HTMLResponse)
def trade_page(order_id: int, request: Request,
               db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = crud.get_order(db, order_id)
    messages = crud.get_messages(db, order_id)
    return templates.TemplateResponse("trade.html", {
        "request": request, "order": order, "messages": messages
    })

@router.post("/pay/{order_id}")
def pay(order_id: int, request: Request, db: Session = Depends(get_db),
        user=Depends(get_current_user)):
    # TODO: заморозить средства
    crud.pay_order(db, order_id, user.id)
    return RedirectResponse(f"/trade/{order_id}", status_code=302)

@router.post("/confirm/{order_id}")
def confirm(order_id: int, request: Request, db: Session = Depends(get_db),
            user=Depends(get_current_user)):
    # TODO: списать, начислить, комиссию
    crud.confirm_order(db, order_id, user.id)
    return RedirectResponse("/orders/mine", status_code=302)

@router.post("/dispute/{order_id}")
def dispute(order_id: int, request: Request, db: Session = Depends(get_db),
            user=Depends(get_current_user)):
    # TODO: пометить спор, заморозить навсегда
    crud.dispute_order(db, order_id, user.id)
    return RedirectResponse(f"/trade/{order_id}", status_code=302)
