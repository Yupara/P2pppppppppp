from flask import Blueprint, request, jsonify
from models import Trade
from database import get_db

public_ads_bp = Blueprint("public_ads", __name__)

@public_ads_bp.route("/create", methods=["POST"])
def create_ad():
    data = request.json
    db = next(get_db())
    
    new_trade = Trade(
        user_id=data["user_id"],
        amount=data["amount"],
        currency=data["currency"],
        payment_method=data["payment_method"],
        status="open"
    )
    db.add(new_trade)
    db.commit()
    return jsonify({"message": "Ad created successfully", "trade_id": new_trade.id})

@public_ads_bp.route("/list", methods=["GET"])
def list_ads():
    db = next(get_db())
    ads = db.query(Trade).filter(Trade.status == "open").all()
    return jsonify([{
        "id": ad.id,
        "amount": ad.amount,
        "currency": ad.currency,
        "payment_method": ad.payment_method
    } for ad in ads])

@public_ads_bp.route("/delete", methods=["POST"])
def delete_ad():
    data = request.json
    db = next(get_db())
    
    ad = db.query(Trade).filter(Trade.id == data["trade_id"]).first()
    if not ad:
        return jsonify({"error": "Ad not found"}), 404
    
    db.delete(ad)
    db.commit()
    return jsonify({"message": "Ad deleted successfully"})
