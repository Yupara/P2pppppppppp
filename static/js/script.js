const API_URL = "https://p2pppppppppp-production.up.railway.app";
let token = localStorage.getItem("token");
let userId = localStorage.getItem("userId");
let language = localStorage.getItem("language") || "ru";

function changeLanguage(lang) {
    language = lang || document.getElementById("language").value;
    localStorage.setItem("language", language);
    updateLanguage();
}

function updateLanguage() {
    const langData = {
        "ru": {
            "register": "Регистрация", "verify": "Верификация", "login": "Вход", "welcome": "Добро пожаловать",
            "balance": "Ваш баланс", "trades": "Сделок завершено", "deposit": "Пополнить баланс",
            "buy-crypto": "Купить криптовалюту", "sell-crypto": "Продать криптовалюту", "create-offer": "Создать заявку",
            "my-offers": "Мои заявки", "chat": "Чат"
        },
        "en": {
            "register": "Register", "verify": "Verify", "login": "Login", "welcome": "Welcome",
            "balance": "Your balance", "trades": "Trades completed", "deposit": "Deposit",
            "buy-crypto": "Buy Crypto", "sell-crypto": "Sell Crypto", "create-offer": "Create Offer",
            "my-offers": "My Offers", "chat": "Chat"
        }
    };
    document.querySelectorAll("[data-lang]").forEach(el => {
        el.textContent = langData[language][el.getAttribute("data-lang")] || el.textContent;
    });
}

if (token && userId) {
    document.getElementById("auth-section").style.display = "none";
    document.getElementById("user-section").style.display = "block";
    document.getElementById("profile-link").style.display = "inline";
    document.getElementById("logout-link").style.display = "inline";
    fetchUserData();
    fetchOffers();
} else {
    document.getElementById("profile-link").style.display = "none";
    document.getElementById("logout-link").style.display = "none";
}

updateLanguage();

async function register() {
    const email = document.getElementById("reg-email").value;
    const phone = document.getElementById("reg-phone").value;
    const password = document.getElementById("reg-password").value;
    console.log("Sending registration:", { email, phone, password });
    try {
        const response = await fetch(`${API_URL}/register`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `email=${encodeURIComponent(email)}&phone=${encodeURIComponent(phone)}&password=${encodeURIComponent(password)}`
        });
        const data = await response.json();
        console.log("Response:", data);
        if (response.ok) {
            document.getElementById("reg-success").textContent = `Код отправлен: ${data.verification_code} / Code sent: ${data.verification_code}`;
            document.getElementById("reg-error").textContent = "";
        } else {
            document.getElementById("reg-error").textContent = data.detail;
            document.getElementById("reg-success").textContent = "";
        }
    } catch (error) {
        console.error("Error:", error);
        document.getElementById("reg-error").textContent = "Ошибка: " + error.message;
    }
}

async function verify() {
    const email = document.getElementById("verify-email").value;
    const code = document.getElementById("verify-code").value;
    const passportInput = document.getElementById("passport-upload");
    const formData = new FormData();
    formData.append("email", email);
    formData.append("code", code);
    if (passportInput.files[0]) formData.append("passport", passportInput.files[0]);
    try {
        const response = await fetch(`${API_URL}/verify`, {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        if (response.ok) {
            document.getElementById("verify-success").textContent = data.message;
            document.getElementById("verify-error").textContent = "";
        } else {
            document.getElementById("verify-error").textContent = data.detail;
            document.getElementById("verify-success").textContent = "";
        }
    } catch (error) {
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
            body: `email=${email}&password=${password}`
        });
        const data = await response.json();
        if (response.ok) {
            token = data.token;
            userId = data.user_id;
            localStorage.setItem("token", token);
            localStorage.setItem("userId", userId);
            document.getElementById("login-success").textContent = "Вход успешен / Login successful";
            document.getElementById("login-error").textContent = "";
            document.getElementById("auth-section").style.display = "none";
            document.getElementById("user-section").style.display = "block";
            document.getElementById("user-email").textContent = email;
            document.getElementById("profile-link").style.display = "inline";
            document.getElementById("logout-link").style.display = "inline";
            fetchUserData();
            fetchOffers();
        } else {
            document.getElementById("login-error").textContent = data.detail;
            document.getElementById("login-success").textContent = "";
        }
    } catch (error) {
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
    document.getElementById("profile-link").style.display = "none";
    document.getElementById("logout-link").style.display = "none";
}

async function fetchUserData() {
    try {
        const response = await fetch(`${API_URL}/user-data?user_id=${userId}&token=${token}`, {
            method: "GET",
            headers: { "Content-Type": "application/x-www-form-urlencoded" }
        });
        const data = await response.json();
        if (response.ok) {
            document.getElementById("user-balance").textContent = data.balance;
            document.getElementById("user-trades").textContent = data.trades_completed;
        }
    } catch (error) {
        console.error("Error fetching user data:", error);
    }
}

async function deposit() {
    const amount = document.getElementById("deposit-amount").value;
    const currency = document.getElementById("deposit-currency").value;
    const network = document.getElementById("deposit-network").value;
    try {
        const response = await fetch(`${API_URL}/deposit`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `user_id=${userId}&amount=${amount}&currency=${currency}&network=${network}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            document.getElementById("deposit-success").textContent = `Баланс пополнен: ${data.new_balance} / Balance updated: ${data.new_balance}`;
            document.getElementById("deposit-error").textContent = "";
            document.getElementById("user-balance").textContent = data.new_balance;
        } else {
            document.getElementById("deposit-error").textContent = data.detail;
            document.getElementById("deposit-success").textContent = "";
        }
    } catch (error) {
        document.getElementById("deposit-error").textContent = "Ошибка: " + error.message;
    }
}

function switchTab(tab) {
    document.getElementById("buy-section").style.display = tab === "buy" ? "block" : "none";
    document.getElementById("sell-section").style.display = tab === "sell" ? "block" : "none";
    document.getElementById("my-offers-section").style.display = tab === "my-offers" ? "block" : "none";
    document.querySelectorAll(".tabs button").forEach(btn => btn.classList.remove("active"));
    document.getElementById(`${tab}-tab`).classList.add("active");
    if (tab === "buy" || tab === "sell") fetchOffers(tab);
    if (tab === "my-offers") fetchMyOffers();
}

async function createOffer() {
    const offerType = document.getElementById("offer-type").value;
    const currency = document.getElementById("offer-currency").value;
    const fiat = document.getElementById("offer-fiat").value;
    const amount = document.getElementById("offer-amount").value;
    const paymentMethod = document.getElementById("offer-payment-method").value;
    const contact = document.getElementById("offer-contact").value;
    try {
        const response = await fetch(`${API_URL}/create-offer`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `user_id=${userId}&offer_type=${offerType}&currency=${currency}&amount=${amount}&fiat=${fiat}&payment_method=${paymentMethod}&contact=${contact}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            document.getElementById("create-offer-success").textContent = "Заявка создана / Offer created";
            document.getElementById("create-offer-error").textContent = "";
            document.getElementById("user-balance").textContent = data.user_balance;
            fetchMyOffers();
        } else {
            document.getElementById("create-offer-error").textContent = data.detail;
            document.getElementById("create-offer-success").textContent = "";
        }
    } catch (error) {
        document.getElementById("create-offer-error").textContent = "Ошибка: " + error.message;
    }
}

async function fetchOffers(offerType) {
    const currency = document.getElementById(offerType === "buy" ? "buy-currency" : "sell-currency").value;
    const fiat = document.getElementById(offerType === "buy" ? "buy-fiat" : "sell-fiat").value;
    const paymentMethod = document.getElementById(offerType === "buy" ? "buy-payment-method" : "sell-payment-method").value;
    const minAmount = document.getElementById(offerType === "buy" ? "buy-amount" : "sell-amount").value;
    try {
        const response = await fetch(`${API_URL}/offers?offer_type=${offerType}&currency=${currency}&fiat=${fiat}&payment_method=${paymentMethod}&min_amount=${minAmount}`);
        const offers = await response.json();
        const offersList = document.getElementById(offerType === "buy" ? "buy-offers-list" : "sell-offers-list");
        offersList.innerHTML = "";
        offers.forEach(offer => {
            if (offer.status === "active") {
                const offerDiv = document.createElement("div");
                offerDiv.className = "offer";
                offerDiv.innerHTML = `
                    <p>ID: ${offer.id}</p>
                    <p>${offerType === "buy" ? "Sell" : "Buy"}: ${offer.sell_amount} ${offer.sell_currency}</p>
                    <p>${offerType === "buy" ? "Buy" : "Sell"}: ${offer.buy_currency}</p>
                    <p>Payment: ${offer.payment_method}</p>
                    <p>Contact: ${offer.contact}</p>
                    <button onclick="buyOffer(${offer.id}, '${offerType}')">${offerType === "buy" ? "Купить / Buy" : "Продать / Sell"}</button>
                `;
                offersList.appendChild(offerDiv);
            }
        });
    } catch (error) {
        console.error("Error fetching offers:", error);
    }
}

async function fetchMyOffers() {
    try {
        const response = await fetch(`${API_URL}/my-offers?user_id=${userId}&token=${token}`);
        const offers = await response.json();
        const offersList = document.getElementById("my-offers-list");
        offersList.innerHTML = "";
        offers.forEach(offer => {
            const offerDiv = document.createElement("div");
            offerDiv.className = "offer";
            offerDiv.innerHTML = `
                <p>ID: ${offer.id}</p>
                <p>Sell: ${offer.sell_amount} ${offer.sell_currency}</p>
                <p>Buy: ${offer.buy_currency}</p>
                <p>Payment: ${offer.payment_method}</p>
                <p>Status: ${offer.status}</p>
                <button onclick="cancelOffer(${offer.id})">Отменить / Cancel</button>
            `;
            offersList.appendChild(offerDiv);
        });
    } catch (error) {
        console.error("Error fetching my offers:", error);
    }
}

async function buyOffer(offerId, offerType) {
    try {
        const response = await fetch(`${API_URL}/buy-offer`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `offer_id=${offerId}&buyer_id=${userId}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            alert("Заявка куплена / Offer bought");
            fetchOffers(offerType);
        } else {
            alert("Ошибка: " + data.detail);
        }
    } catch (error) {
        alert("Ошибка: " + error.message);
    }
}

async function cancelOffer(offerId) {
    try {
        const response = await fetch(`${API_URL}/cancel-offer`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `offer_id=${offerId}&user_id=${userId}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            alert("Заявка отменена / Offer cancelled");
            fetchMyOffers();
        } else {
            alert("Ошибка: " + data.detail);
        }
    } catch (error) {
        alert("Ошибка: " + error.message);
    }
}

async function sendMessage() {
    const offerId = document.getElementById("chat-section").getAttribute("data-offer-id");
    const text = document.getElementById("chat-input").value;
    try {
        const response = await fetch(`${API_URL}/send-message`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `offer_id=${offerId}&user_id=${userId}&text=${encodeURIComponent(text)}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            document.getElementById("chat-input").value = "";
            fetchMessages(offerId);
        } else {
            alert("Ошибка: " + data.detail);
        }
    } catch (error) {
        alert("Ошибка: " + error.message);
    }
}

async function fetchMessages(offerId) {
    try {
        const response = await fetch(`${API_URL}/get-messages?offer_id=${offerId}&user_id=${userId}&token=${token}`);
        const messages = await response.json();
        const chatMessages = document.getElementById("chat-messages");
        chatMessages.innerHTML = "";
        messages.forEach(msg => {
            const messageDiv = document.createElement("div");
            messageDiv.className = "chat-message " + (msg.user_id === userId ? "sent" : "received");
            messageDiv.textContent = msg.text;
            chatMessages.appendChild(messageDiv);
        });
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (error) {
        console.error("Error fetching messages:", error);
    }
}

function openChat(offerId) {
    document.getElementById("chat-section").style.display = "block";
    document.getElementById("chat-section").setAttribute("data-offer-id", offerId);
    fetchMessages(offerId);
}

function openSupport() {
    const message = prompt("Введите сообщение для поддержки / Enter message for support:");
    if (message) {
        fetch(`${API_URL}/support`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `user_id=${userId}&message=${encodeURIComponent(message)}&token=${token}`
        }).then(response => response.json()).then(data => {
            alert(data.message);
        }).catch(error => alert("Ошибка: " + error.message));
    }
}

function openProfile() {
    // Пока просто заглушка
    alert("Профиль / Profile (в разработке)");
}
