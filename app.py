from flask import Flask
from routes.auth import auth_bp
from routes.trades import trades_bp
from routes.admin import admin_bp

app = Flask(__name__)

# Регистрируем маршруты
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(trades_bp, url_prefix="/trades")
app.register_blueprint(admin_bp, url_prefix="/admin")

if __name__ == "__main__":
    app.run(debug=True)
