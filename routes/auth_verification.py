from flask import Blueprint, request, jsonify
import random
from scripts.sms_verification import send_sms
from models import User
from database import get_db

auth_verification_bp = Blueprint("auth_verification", __name__)

@auth_verification_bp.route("/send_sms_code", methods=["POST"])
def send_sms_code():
    data = request.json
    phone_number = data["phone_number"]
    code = random.randint(100000, 999999)  # Генерируем 6-значный код
    
    response = send_sms(phone_number, code)
    if "error" in response:
        return jsonify(response), 400
    
    return jsonify({"message": "Verification code sent", "code": code})  # Код отправлен

@auth_verification_bp.route("/verify_sms_code", methods=["POST"])
def verify_sms_code():
    data = request.json
    db = next(get_db())
    
    user = db.query(User).filter(User.phone_number == data["phone_number"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Сравниваем код
    if data["code"] == user.verification_code:
        user.is_verified = True
        db.commit()
        return jsonify({"message": "User verified successfully"})
    else:
        return jsonify({"error": "Invalid verification code"}), 400
