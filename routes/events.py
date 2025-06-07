from flask import Blueprint, request, jsonify
from models import Event
from database import get_db

events_bp = Blueprint("events", __name__)

@events_bp.route("/create", methods=["POST"])
def create_event():
    data = request.json
    db = next(get_db())

    new_event = Event(
        name=data["name"],
        description=data["description"],
        start_time=data["start_time"],
        end_time=data["end_time"]
    )
    db.add(new_event)
    db.commit()
    return jsonify({"message": "Event created successfully", "event_id": new_event.id})

@events_bp.route("/list", methods=["GET"])
def list_events():
    db = next(get_db())
    events = db.query(Event).all()
    return jsonify([{
        "id": event.id,
        "name": event.name,
        "description": event.description,
        "start_time": event.start_time,
        "end_time": event.end_time
    } for event in events])
