from flask import Blueprint, request, jsonify
from models import User, Referral
from database import get_db

referrals_bp = Blueprint("referrals", __name__)

@referrals_bp.route("/earnings", methods=["GET"])
def referral_earnings():
    user_id = request.args.get("user_id")
    db = next(get_db())
    
    referrals = db.query(Referral).filter(Referral.user_id == user_id).all()
    total_earnings = sum(ref.earned_commission for ref in referrals)
    return jsonify({"total_earnings": total_earnings})

@referrals_bp.route("/add", methods=["POST"])
def add_referral():
    data = request.json
    db = next(get_db())
    
    new_referral = Referral(
        user_id=data["user_id"],
        referred_user_id=data["referred_user_id"],
        earned_commission=data["earned_commission"]
    )
    db.add(new_referral)
    db.commit()
    return jsonify({"message": "Referral added successfully"})
