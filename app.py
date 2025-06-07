from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///p2p_platform.db'
db = SQLAlchemy(app)

# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)

# Модель объявления
class Ad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    payment_methods = db.Column(db.String(100), nullable=False)
    limits = db.Column(db.String(100), nullable=False)

# Маршруты приложения
@app.route("/")
def index():
    ads = Ad.query.all()
    return render_template("index.html", ads=ads)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        else:
            return "Неверные данные"
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" in session:
        ads = Ad.query.filter_by(user_id=session["user_id"]).all()
        return render_template("dashboard.html", ads=ads)
    return redirect(url_for("login"))

@app.route("/create_ad", methods=["GET", "POST"])
def create_ad():
    if "user_id" in session:
        if request.method == "POST":
            currency = request.form["currency"]
            amount = request.form["amount"]
            price = request.form["price"]
            payment_methods = request.form["payment_methods"]
            limits = request.form["limits"]
            ad = Ad(user_id=session["user_id"], currency=currency, amount=amount,
                    price=price, payment_methods=payment_methods, limits=limits)
            db.session.add(ad)
            db.session.commit()
            return redirect(url_for("dashboard"))
        return render_template("create_ad.html")
    return redirect(url_for("login"))

@app.route("/buy/<int:ad_id>")
def buy(ad_id):
    if "user_id" in session:
        ad = Ad.query.get(ad_id)
        if ad:
            return f"Вы покупаете {ad.amount} {ad.currency} по цене {ad.price}"
        return "Объявление не найдено"
    return redirect(url_for("login"))

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
