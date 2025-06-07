from flask import Blueprint, request, jsonify
from models import Task, User
from database import get_db

tasks_bp = Blueprint("tasks", __name__)

@tasks_bp.route("/create", methods=["POST"])
def create_task():
    data = request.json
    db = next(get_db())
    
    user = db.query(User).filter(User.id == data["user_id"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    new_task = Task(
        user_id=data["user_id"],
        description=data["description"],
        status="pending"
    )
    db.add(new_task)
    db.commit()
    return jsonify({"message": "Task created successfully", "task_id": new_task.id})

@tasks_bp.route("/list", methods=["GET"])
def list_tasks():
    user_id = request.args.get("user_id")
    db = next(get_db())

    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    return jsonify([{
        "id": task.id,
        "description": task.description,
        "status": task.status,
        "created_at": task.created_at
    } for task in tasks])

@tasks_bp.route("/update_status", methods=["POST"])
def update_task_status():
    data = request.json
    db = next(get_db())

    task = db.query(Task).filter(Task.id == data["task_id"]).first()
    if not task:
        return jsonify({"error": "Task not found"}), 404

    task.status = data["status"]
    db.commit()
    return jsonify({"message": "Task status updated successfully"})
