import requests

def send_sms(phone_number, code):
    # Используем сторонний сервис для отправки SMS
    sms_api_url = "https://example-sms-api.com/send"
    payload = {
        "phone_number": phone_number,
        "message": f"Your verification code is: {code}"
    }
    headers = {
        "Authorization": "Bearer YOUR_SMS_API_KEY",
        "Content-Type": "application/json"
    }
    
    response = requests.post(sms_api_url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return {"message": "SMS sent successfully"}
    else:
        return {"error": "Failed to send SMS", "details": response.text}
