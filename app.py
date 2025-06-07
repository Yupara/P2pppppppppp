import os
from flask import Flask, redirect
from flask_socketio import SocketIO

# Импортируем маршруты
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
from routes.profile import profile_bp
from routes.public_ads import public_ads_bp
from routes.currencies import currencies_bp
from routes.webhooks import webhooks_bp
from routes.analytics import analytics_bp
from routes.notifications import notifications_bp
from routes.roles import roles_bp
from routes.tasks import tasks_bp
from routes.events import events_bp
from routes.audit_logs import audit_logs_bp
from routes.realtime_notifications import realtime_notifications_bp
from routes.files import files_bp
from routes.email_notifications import email_notifications_bp

app = Flask(__name__)
socketio = SocketIO(app)

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
app.register_blueprint(auth_verification_bp, url_prefix="/auth_verification")
app.register_blueprint(referral_payouts_bp, url_prefix="/referral_payouts")
app.register_blueprint(profile_bp, url_prefix="/profile")
app.register_blueprint(public_ads_bp, url_prefix="/public_ads")
app.register_blueprint(currencies_bp, url_prefix="/currencies")
app.register_blueprint(webhooks_bp, url_prefix="/webhooks")
app.register_blueprint(analytics_bp, url_prefix="/analytics")
app.register_blueprint(notifications_bp, url_prefix="/notifications")
app.register_blueprint(roles_bp, url_prefix="/roles")
app.register_blueprint(tasks_bp, url_prefix="/tasks")
app.register_blueprint(events_bp, url_prefix="/events")
app.register_blueprint(audit_logs_bp, url_prefix="/audit_logs")
app.register_blueprint(realtime_notifications_bp, url_prefix="/realtime_notifications")
app.register_blueprint(files_bp, url_prefix="/files")
app.register_blueprint(email_notifications_bp, url_prefix="/email_notifications")

# Главная страница перенаправляет сразу на ваш сайт
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def redirect_to_external(path):
    return redirect("https://p2pppppppppp-production.up.railway.app/", code=302)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
