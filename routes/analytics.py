from flask import Blueprint, jsonify
from models import Trade, User
from database import get_db

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/overview", methods=["GET"])
def get_overview():
    db = next(get_db())

    total_users = db.query(User).count()
    total_trades = db.query(Trade).count()
    completed_trades = db.query(Trade).filter(Trade.status == "completed").count()
    open_trades = db.query(Trade).filter(Trade.status == "open").count()

    return jsonify({
        "total_users": total_users,
        "total_trades": total_trades,
        "completed_trades": completed_trades,
        "open_trades": open_trades
    })

@analytics_bp.route("/revenue", methods=["GET"])
def get_revenue():
    db = next(get_db())
    completed_trades = db.query(Trade).filter(Trade.status == "completed").all()

    total_revenue = sum(trade.amount * 0.005 for trade in completed_trades)
    return jsonify({"total_revenue": total_revenue})
