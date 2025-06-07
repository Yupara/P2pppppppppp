from flask import Blueprint, request, jsonify
from models import Currency
from database import get_db

currencies_bp = Blueprint("currencies", __name__)

@currencies_bp.route("/add", methods=["POST"])
def add_currency():
    data = request.json
    db = next(get_db())
    
    new_currency = Currency(
        name=data["name"],
        symbol=data["symbol"],
        rate_to_usdt=data["rate_to_usdt"]
    )
    db.add(new_currency)
    db.commit()
    return jsonify({"message": "Currency added successfully"})

@currencies_bp.route("/list", methods=["GET"])
def list_currencies():
    db = next(get_db())
    currencies = db.query(Currency).all()
    return jsonify([{
        "id": currency.id,
        "name": currency.name,
        "symbol": currency.symbol,
        "rate_to_usdt": currency.rate_to_usdt
    } for currency in currencies])

@currencies_bp.route("/delete", methods=["POST"])
def delete_currency():
    data = request.json
    db = next(get_db())
    
    currency = db.query(Currency).filter(Currency.id == data["currency_id"]).first()
    if not currency:
        return jsonify({"error": "Currency not found"}), 404
    
    db.delete(currency)
    db.commit()
    return jsonify({"message": "Currency deleted successfully"})
