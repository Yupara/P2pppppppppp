const API_URL = "https://p2pppppppppp-production.up.railway.app";
let token = localStorage.getItem("token");
let userId = localStorage.getItem("userId");

if (token && userId) {
    document.getElementById("auth-section").style.display = "none";
    document.getElementById("user-section").style.display = "block";
    fetchOffers();
}

async function register() {
    const email = document.getElementById("reg-email").value;
    const phone = document.getElementById("reg-phone").value;
    const password = document.getElementById("reg-password").value;
    console.log("Sending registration:", { email, phone, password }); // Отладка
    try {
        const response = await fetch(`${API_URL}/register`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `email=${encodeURIComponent(email)}&phone=${encodeURIComponent(phone)}&password=${encodeURIComponent(password)}`
        });
        const data = await response.json();
        console.log("Response:", data); // Отладка
        if (response.ok) {
            document.getElementById("reg-success").textContent = `Код отправлен: ${data.verification_code}`;
            document.getElementById("reg-error").textContent = "";
        } else {
            document.getElementById("reg-error").textContent = data.detail;
            document.getElementById("reg-success").textContent = "";
        }
    } catch (error) {
        console.error("Error:", error); // Отладка
        document.getElementById("reg-error").textContent = "Ошибка: " + error.message;
    }
}

async function verify() {
    const email = document.getElementById("verify-email").value;
    const code = document.getElementById("verify-code").value;
    try {
        const response = await fetch(`${API_URL}/verify`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `email=${encodeURIComponent(email)}&code=${encodeURIComponent(code)}`
        });
        const data = await response.json();
        console.log("Response:", data); // Отладка
        if (response.ok) {
            document.getElementById("verify-success").textContent = "Верификация успешна";
            document.getElementById("verify-error").textContent = "";
        } else {
            document.getElementById("verify-error").textContent = data.detail;
            document.getElementById("verify-success").textContent = "";
        }
    } catch (error) {
        console.error("Error:", error); // Отладка
        document.getElementById("verify-error").textContent = "Ошибка: " + error.message;
    }
}

async function login() {
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;
    try {
        const response = await fetch(`${API_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
        });
        const data = await response.json();
        console.log("Response:", data); // Отладка
        if (response.ok) {
            token = data.token;
            userId = data.user_id;
            localStorage.setItem("token", token);
            localStorage.setItem("userId", userId);
            document.getElementById("login-success").textContent = "Вход успешен";
            document.getElementById("login-error").textContent = "";
            document.getElementById("auth-section").style.display = "none";
            document.getElementById("user-section").style.display = "block";
            document.getElementById("user-email").textContent = email;
            fetchOffers();
        } else {
            document.getElementById("login-error").textContent = data.detail;
            document.getElementById("login-success").textContent = "";
        }
    } catch (error) {
        console.error("Error:", error); // Отладка
        document.getElementById("login-error").textContent = "Ошибка: " + error.message;
    }
}

function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("userId");
    token = null;
    userId = null;
    document.getElementById("auth-section").style.display = "block";
    document.getElementById("user-section").style.display = "none";
}

async function deposit() {
    const amount = document.getElementById("deposit-amount").value;
    try {
        const response = await fetch(`${API_URL}/deposit`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `user_id=${userId}&amount=${encodeURIComponent(amount)}&token=${encodeURIComponent(token)}`
        });
        const data = await response.json();
        console.log("Response:", data); // Отладка
        if (response.ok) {
            document.getElementById("deposit-success").textContent = `Баланс пополнен: ${data.new_balance}`;
            document.getElementById("deposit-error").textContent = "";
            document.getElementById("user-balance").textContent = data.new_balance;
        } else {
            document.getElementById("deposit-error").textContent = data.detail;
            document.getElementById("deposit-success").textContent = "";
        }
    } catch (error) {
        console.error("Error:", error); // Отладка
        document.getElementById("deposit-error").textContent = "Ошибка: " + error.message;
    }
}

async function createOffer() {
    const sellCurrency = document.getElementById("sell-currency").value;
    const sellAmount = document.getElementById("sell-amount").value;
    const buyCurrency = document.getElementById("buy-currency").value;
    const paymentMethod = document.getElementById("payment-method").value;
    const contact = document.getElementById("contact").value;
    try {
        const response = await fetch(`${API_URL}/create-offer`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `user_id=${userId}&sell_currency=${encodeURIComponent(sellCurrency)}&sell_amount=${encodeURIComponent(sellAmount)}&buy_currency=${encodeURIComponent(buyCurrency)}&payment_method=${encodeURIComponent(paymentMethod)}&contact=${encodeURIComponent(contact)}&token=${encodeURIComponent(token)}`
        });
        const data = await response.json();
        console.log("Response:", data); // Отладка
        if (response.ok) {
            document.getElementById("create-offer-success").textContent = "Заявка создана";
            document.getElementById("create-offer-error").textContent = "";
            document.getElementById("user-balance").textContent = data.seller_balance;
            fetchOffers();
        } else {
            document.getElementById("create-offer-error").textContent = data.detail;
            document.getElementById("create-offer-success").textContent = "";
        }
    } catch (error) {
        console.error("Error:", error); // Отладка
        document.getElementById("create-offer-error").textContent = "Ошибка: " + error.message;
    }
}

async function fetchOffers() {
    try {
        const response = await fetch(`${API_URL}/offers`);
        const offers = await response.json();
        console.log("Offers:", offers); // Отладка
        const offersList = document.getElementById("offers-list");
        offersList.innerHTML = "";
        offers.forEach(offer => {
            const offerDiv = document.createElement("div");
            offerDiv.className = "offer";
            offerDiv.innerHTML = `
                <p>ID: ${offer.id}</p>
                <p>Продажа: ${offer.sell_amount} ${offer.sell_currency}</p>
                <p>Покупка: ${offer.buy_currency}</p>
                <p>Метод оплаты: ${offer.payment_method}</p>
                <p>Контакт: ${offer.contact}</p>
                <button onclick="dealOffer(${offer.id})">Купить</button>
            `;
            offersList.appendChild(offerDiv);
        });
    } catch (error) {
        console.error("Error:", error); // Отладка
    }
}

async function dealOffer(offerId) {
    try {
        const response = await fetch(`${API_URL}/buy-offer`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `offer_id=${encodeURIComponent(offerId)}&buyer_id=${encodeURIComponent(userId)}&token=${encodeURIComponent(token)}`
        });
        const data = await response.json();
        console.log("Response:", data); // Отладка
        if (response.ok) {
            alert("Заявка куплена");
            fetchOffers();
        } else {
            alert("Ошибка: " + data.detail);
        }
    } catch (error) {
        console.error("Error:", error); // Отладка
        alert("Ошибка: " + error.message);
    }
}
