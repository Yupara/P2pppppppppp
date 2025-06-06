from flask import Blueprint, request, jsonify
from models import User
from database import get_db

balance_bp = Blueprint("balance", __name__)

@balance_bp.route("/add_balance", methods=["POST"])
def add_balance():
    data = request.json
    db = next(get_db())
    
    user = db.query(User).filter(User.id == data["user_id"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user.balance_usdt += data["amount"]
    db.commit()
    return jsonify({"message": f"Balance updated. New balance: {user.balance_usdt} USDT"})

@balance_bp.route("/withdraw_balance", methods=["POST"])
def withdraw_balance():
    data = request.json
    db = next(get_db())
    
    user = db.query(User).filter(User.id == data["user_id"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if user.balance_usdt < data["amount"]:
        return jsonify({"error": "Insufficient balance"}), 400
    
    user.balance_usdt -= data["amount"]
    db.commit()
    return jsonify({"message": f"Withdrawal successful. Remaining balance: {user.balance_usdt} USDT"})
