from flask import Blueprint, jsonify, request
from models import AuditLog
from database import get_db

audit_logs_bp = Blueprint("audit_logs", __name__)

@audit_logs_bp.route("/list", methods=["GET"])
def list_audit_logs():
    db = next(get_db())
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
    return jsonify([{
        "id": log.id,
        "user_id": log.user_id,
        "action": log.action,
        "description": log.description,
        "timestamp": log.timestamp
    } for log in logs])

@audit_logs_bp.route("/create", methods=["POST"])
def create_audit_log():
    data = request.json
    db = next(get_db())

    new_log = AuditLog(
        user_id=data["user_id"],
        action=data["action"],
        description=data["description"]
    )
    db.add(new_log)
    db.commit()
    return jsonify({"message": "Audit log created successfully"})
