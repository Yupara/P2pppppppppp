from flask import Blueprint, request, jsonify
from models import Ad, Trade, db

router = Blueprint("trades", __name__)

@router.route("/api/buy", methods=["POST"])
def buy():
    data = request.json
    ad_id = data.get("adId")
    ad = Ad.query.get(ad_id)
    if ad:
        # Логика обработки сделки
        trade = Trade(ad_id=ad_id, buyer_id=1, amount=ad.amount)  # пример buyer_id
        db.session.add(trade)
        db.session.commit()
        return jsonify({"message": "Сделка успешно завершена"})
    return jsonify({"error": "Объявление не найдено"}), 404
