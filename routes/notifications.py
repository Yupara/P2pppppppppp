from flask import Blueprint, request, jsonify
from models import Notification, User
from database import get_db

notifications_bp = Blueprint("notifications", __name__)

@notifications_bp.route("/create", methods=["POST"])
def create_notification():
    data = request.json
    db = next(get_db())

    user = db.query(User).filter(User.id == data["user_id"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    new_notification = Notification(
        user_id=data["user_id"],
        message=data["message"],
        type=data["type"]
    )
    db.add(new_notification)
    db.commit()
    return jsonify({"message": "Notification created successfully"})

@notifications_bp.route("/list", methods=["GET"])
def list_notifications():
    user_id = request.args.get("user_id")
    db = next(get_db())

    notifications = db.query(Notification).filter(Notification.user_id == user_id).all()
    return jsonify([{
        "id": notification.id,
        "message": notification.message,
        "type": notification.type,
        "created_at": notification.created_at
    } for notification in notifications])
