import datetime
from flask import Blueprint, jsonify
from models import Trade
from database import get_db

auto_cancel_bp = Blueprint("auto_cancel", __name__)

@auto_cancel_bp.route("/cancel_inactive_trades", methods=["POST"])
def cancel_inactive_trades():
    db = next(get_db())
    now = datetime.datetime.utcnow()
    
    # Ищем сделки, которые открыты более 30 минут
    inactive_trades = db.query(Trade).filter(
        Trade.status == "open",
        Trade.created_at <= now - datetime.timedelta(minutes=30)
    ).all()
    
    for trade in inactive_trades:
        trade.status = "cancelled"
    
    db.commit()
    return jsonify({"message": f"{len(inactive_trades)} inactive trades cancelled"})
