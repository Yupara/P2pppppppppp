from flask import Blueprint, request, jsonify
from models import Role, User
from database import get_db

roles_bp = Blueprint("roles", __name__)

@roles_bp.route("/assign", methods=["POST"])
def assign_role():
    data = request.json
    db = next(get_db())

    user = db.query(User).filter(User.id == data["user_id"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    role = db.query(Role).filter(Role.name == data["role_name"]).first()
    if not role:
        return jsonify({"error": "Role not found"}), 404

    user.role_id = role.id
    db.commit()
    return jsonify({"message": f"Role '{role.name}' assigned to user '{user.username}'"})

@roles_bp.route("/check_permission", methods=["POST"])
def check_permission():
    data = request.json
    db = next(get_db())

    user = db.query(User).filter(User.id == data["user_id"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    role = db.query(Role).filter(Role.id == user.role_id).first()
    if not role:
        return jsonify({"error": "Role not found"}), 404

    if data["permission"] in role.permissions:
        return jsonify({"message": "Permission granted"})
    else:
        return jsonify({"error": "Permission denied"}), 403
