from flask import Blueprint, jsonify
from flask_socketio import SocketIO, emit

socketio = SocketIO()
realtime_notifications_bp = Blueprint("realtime_notifications", __name__)

@socketio.on("send_notification")
def handle_send_notification(data):
    emit("receive_notification", data, broadcast=True)

@realtime_notifications_bp.route("/test", methods=["GET"])
def test_realtime():
    return jsonify({"message": "Real-time notifications are active"})
