from flask import Blueprint, request, jsonify
from models import Trade, User
from database import get_db

disputes_bp = Blueprint("disputes", __name__)

@disputes_bp.route("/create", methods=["POST"])
def create_dispute():
    data = request.json
    db = next(get_db())
    
    trade = db.query(Trade).filter(Trade.id == data["trade_id"]).first()
    if not trade or trade.status != "completed":
        return jsonify({"error": "Trade not found or not completed"}), 404
    
    trade.status = "dispute"
    db.commit()
    return jsonify({"message": "Dispute created successfully"})

@disputes_bp.route("/resolve", methods=["POST"])
def resolve_dispute():
    data = request.json
    db = next(get_db())
    
    trade = db.query(Trade).filter(Trade.id == data["trade_id"]).first()
    if not trade or trade.status != "dispute":
        return jsonify({"error": "Dispute not found"}), 404
    
    resolution = data["resolution"]  # "approve_buyer" or "approve_seller"
    if resolution == "approve_buyer":
        trade.status = "completed_buyer"
    elif resolution == "approve_seller":
        trade.status = "completed_seller"
    else:
        return jsonify({"error": "Invalid resolution"}), 400
    
    db.commit()
    return jsonify({"message": "Dispute resolved successfully"})
