from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import random

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_email_password'

db = SQLAlchemy(app)
mail = Mail(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    verification_code = db.Column(db.String(6))
    is_verified = db.Column(db.Boolean, default=False)

# Endpoint: Registration
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'User already exists'}), 400

    # Generate verification code
    verification_code = str(random.randint(100000, 999999))

    # Create user
    new_user = User(email=email, password=password, verification_code=verification_code)
    db.session.add(new_user)
    db.session.commit()

    # Send verification email
    msg = Message('Verify Your Account', sender='your_email@gmail.com', recipients=[email])
    msg.body = f'Your verification code is {verification_code}'
    mail.send(msg)

    return jsonify({'message': 'User registered. Please verify your email.'}), 201

# Endpoint: Verify Email
@app.route('/verify', methods=['POST'])
def verify_email():
    data = request.json
    email = data.get('email')
    code = data.get('verification_code')

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.verification_code == code:
        user.is_verified = True
        db.session.commit()
        return jsonify({'message': 'Email verified successfully.'}), 200
    else:
        return jsonify({'error': 'Invalid verification code'}), 400

# Endpoint: Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email, password=password).first()
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user.is_verified:
        return jsonify({'error': 'Email not verified'}), 403

    return jsonify({'message': 'Login successful'}), 200

if __name__ == '__main__':
    db.create_all()  # Create database tables
    app.run(debug=True)
