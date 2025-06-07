user = User(username="TestUser", password="12345")
db.session.add(user)
db.session.commit()

ad = Ad(user_id=user.id, currency="USDT", amount=1000, price=70.96,
        payment_methods="SBP, Тинькофф", limits="500 — 500000")
db.session.add(ad)
db.session.commit()
