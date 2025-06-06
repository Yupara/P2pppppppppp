from flask import Blueprint, jsonify, request
from models import Trade, User
from database import get_db
from scripts.notifications import notify_large_trade

large_trades_bp = Blueprint("large_trades", __name__)

@large_trades_bp.route("/check_large_trade", methods=["POST"])
def check_large_trade():
    data = request.json
    db = next(get_db())
    
    trade = db.query(Trade).filter(Trade.id == data["trade_id"]).first()
    if not trade:
        return jsonify({"error": "Trade not found"}), 404
    
    if trade.amount >= 10000:  # Порог крупной сделки
        user_email = db.query(User).filter(User.id == trade.user_id).first().email
        notify_large_trade(user_email, trade.id, trade.amount)
        return jsonify({"message": "Large trade notification sent"})
    
    return jsonify({"message": "Trade amount is below the large trade threshold"})
