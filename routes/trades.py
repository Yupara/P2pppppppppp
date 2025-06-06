from flask import Blueprint, request, jsonify
from models import Trade, User
from database import get_db

trades_bp = Blueprint("trades", __name__)

@trades_bp.route("/create", methods=["POST"])
def create_trade():
    data = request.json
    db = next(get_db())
    
    user = db.query(User).filter(User.id == data["user_id"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    new_trade = Trade(
        user_id=data["user_id"],
        amount=data["amount"],
        currency=data["currency"],
        payment_method=data["payment_method"]
    )
    db.add(new_trade)
    db.commit()
    return jsonify({"message": "Trade created successfully", "trade_id": new_trade.id})

@trades_bp.route("/list", methods=["GET"])
def list_trades():
    db = next(get_db())
    trades = db.query(Trade).filter(Trade.status == "open").all()
    return jsonify([{
        "id": trade.id,
        "user_id": trade.user_id,
        "amount": trade.amount,
        "currency": trade.currency,
        "payment_method": trade.payment_method,
        "status": trade.status
    } for trade in trades])
