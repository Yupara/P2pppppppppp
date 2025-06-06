from flask import Blueprint, request, jsonify
from models import User
from database import get_db

user_management_bp = Blueprint("user_management", __name__)

@user_management_bp.route("/block", methods=["POST"])
def block_user():
    data = request.json
    db = next(get_db())
    
    user = db.query(User).filter(User.id == data["user_id"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user.is_blocked = True
    db.commit()
    return jsonify({"message": "User blocked successfully"})

@user_management_bp.route("/unblock", methods=["POST"])
def unblock_user():
    data = request.json
    db = next(get_db())
    
    user = db.query(User).filter(User.id == data["user_id"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user.is_blocked = False
    db.commit()
    return jsonify({"message": "User unblocked successfully"})
