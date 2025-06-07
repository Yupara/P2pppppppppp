from flask import Blueprint, request, jsonify
import json

webhooks_bp = Blueprint("webhooks", __name__)

@webhooks_bp.route("/setup", methods=["POST"])
def setup_webhook():
    data = request.json
    # Пример настройки вебхука
    webhook_url = data.get("webhook_url")
    if not webhook_url:
        return jsonify({"error": "Webhook URL is required"}), 400

    # Логика сохранения вебхука
    with open("webhooks.json", "w") as f:
        json.dump({"webhook_url": webhook_url}, f)
    
    return jsonify({"message": "Webhook setup successfully"})

@webhooks_bp.route("/trigger", methods=["POST"])
def trigger_webhook():
    with open("webhooks.json", "r") as f:
        webhook_data = json.load(f)
    webhook_url = webhook_data.get("webhook_url")

    if not webhook_url:
        return jsonify({"error": "Webhook URL not configured"}), 400

    # Пример отправки данных на вебхук
    data = request.json
    response = requests.post(webhook_url, json=data)

    if response.status_code == 200:
        return jsonify({"message": "Webhook triggered successfully"})
    else:
        return jsonify({"error": "Failed to trigger webhook", "details": response.text}), 500
