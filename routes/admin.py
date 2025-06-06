from flask import Blueprint, request, jsonify
from models import User, Trade
from database import get_db

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/users", methods=["GET"])
def list_users():
    db = next(get_db())
    users = db.query(User).all()
    return jsonify([{
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_verified": user.is_verified,
        "balance_usdt": user.balance_usdt
    } for user in users])

@admin_bp.route("/verify_user", methods=["POST"])
def verify_user():
    data = request.json
    db = next(get_db())
    
    user = db.query(User).filter(User.id == data["user_id"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user.is_verified = True
    db.commit()
    return jsonify({"message": "User verified successfully"})
