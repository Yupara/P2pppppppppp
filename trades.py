@router.post("/buy")
def buy(ad_id: int, user_id: int, amount: float):
    # Логика для обработки покупки
    trade = Trade(ad_id=ad_id, buyer_id=user_id, amount=amount)
    db.session.add(trade)
    db.session.commit()
    return {"message": "Сделка завершена"}
