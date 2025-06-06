from flask import Flask
from routes.auth import auth_bp
from routes.trades import trades_bp
from routes.admin import admin_bp
from routes.disputes import disputes_bp
from routes.referrals import referrals_bp
from routes.user_management import user_management_bp
from routes.large_trades import large_trades_bp
from routes.auto_cancel import auto_cancel_bp
from routes.balance import balance_bp

app = Flask(__name__)

# Регистрируем маршруты
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(trades_bp, url_prefix="/trades")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(disputes_bp, url_prefix="/disputes")
app.register_blueprint(referrals_bp, url_prefix="/referrals")
app.register_blueprint(user_management_bp, url_prefix="/user_management")
app.register_blueprint(large_trades_bp, url_prefix="/large_trades")
app.register_blueprint(auto_cancel_bp, url_prefix="/auto_cancel")
app.register_blueprint(balance_bp, url_prefix="/balance")

if __name__ == "__main__":
    app.run(debug=True)
