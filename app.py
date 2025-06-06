from flask import Flask
from routes.auth import auth_bp
from routes.trades import trades_bp
from routes.admin import admin_bp
from routes.disputes import disputes_bp
from routes.referrals import referrals_bp
from routes.user_management import user_management_bp

app = Flask(__name__)

# Регистрируем маршруты
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(trades_bp, url_prefix="/trades")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(disputes_bp, url_prefix="/disputes")
app.register_blueprint(referrals_bp, url_prefix="/referrals")
app.register_blueprint(user_management_bp, url_prefix="/user_management")

if __name__ == "__main__":
    app.run(debug=True)
