from flask import Blueprint, request, jsonify
from models import Referral, User
from database import get_db

referral_payouts_bp = Blueprint("referral_payouts", __name__)

@referral_payouts_bp.route("/pay_referral", methods=["POST"])
def pay_referral():
    data = request.json
    db = next(get_db())
    
    referral = db.query(Referral).filter(Referral.user_id == data["user_id"]).first()
    if not referral:
        return jsonify({"error": "Referral not found"}), 404

    user = db.query(User).filter(User.id == referral.user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Добавляем комиссию к балансу
    user.balance_usdt += referral.earned_commission
    referral.earned_commission = 0.0  # Обнуляем после выплаты
    db.commit()
    
    return jsonify({"message": "Referral payout completed", "new_balance": user.balance_usdt})
