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
from routes.auth_verification import auth_verification_bp
from routes.referral_payouts import referral_payouts_bp

app = Flask(__name__)

# Регистрируем маршруты
app.register_blueprint(auth_bp, url_prefix="/auth")  # Авторизация и регистрация
app.register_blueprint(trades_bp, url_prefix="/trades")  # Работа с объявлениями
app.register_blueprint(admin_bp, url_prefix="/admin")  # Администраторский кабинет
app.register_blueprint(disputes_bp, url_prefix="/disputes")  # Система споров
app.register_blueprint(referrals_bp, url_prefix="/referrals")  # Реферальная программа
app.register_blueprint(user_management_bp, url_prefix="/user_management")  # Управление пользователями
app.register_blueprint(large_trades_bp, url_prefix="/large_trades")  # Крупные сделки
app.register_blueprint(auto_cancel_bp, url_prefix="/auto_cancel")  # Автоматическая отмена сделок
app.register_blueprint(balance_bp, url_prefix="/balance")  # Баланс пользователя
app.register_blueprint(auth_verification_bp, url_prefix="/auth_verification")  # Верификация через SMS
app.register_blueprint(referral_payouts_bp, url_prefix="/referral_payouts")  # Реферальные выплаты

if __name__ == "__main__":
    app.run(debug=True)
