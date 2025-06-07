from flask import Blueprint, jsonify, request
from models import User
from database import get_db

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/view", methods=["GET"])
def view_profile():
    user_id = request.args.get("user_id")
    db = next(get_db())
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone_number": user.phone_number,
        "balance_usdt": user.balance_usdt,
        "is_verified": user.is_verified
    })

@profile_bp.route("/update", methods=["POST"])
def update_profile():
    data = request.json
    db = next(get_db())
    
    user = db.query(User).filter(User.id == data["user_id"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]
    if "phone_number" in data:
        user.phone_number = data["phone_number"]
    
    db.commit()
    return jsonify({"message": "Profile updated successfully"})
