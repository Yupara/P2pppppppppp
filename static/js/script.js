const API_URL = "https://p2pppppppppp-production.up.railway.app";
let token = localStorage.getItem("token");
let userId = localStorage.getItem("userId");
let isAdmin = localStorage.getItem("isAdmin") === "true";
let currentOfferId = null;
let currentTab = "buy";
let language = "ru";
let chatInterval = null;

if (token && userId) {
    document.getElementById("auth-section").style.display = "none";
    document.getElementById("user-section").style.display = "block";
    document.getElementById("logout-link").style.display = "inline";
    document.getElementById("profile-link").style.display = "inline";
    if (isAdmin) {
        document.getElementById("admin-section").style.display = "block";
        fetchAdminStats();
        fetchUsers();
        fetchLargeTrades();
    }
    fetchOffers();
    fetchMyOffers();
    changeLanguage();
}

document.getElementById("deposit-currency").addEventListener("change", function() {
    const currency = this.value;
    const networkSelect = document.getElementById("deposit-network");
    if (currency !== "fiat") {
        networkSelect.style.display = "block";
    } else {
        networkSelect.style.display = "none";
    }
});

async function register() {
    const email = document.getElementById("reg-email").value;
    const phone = document.getElementById("reg-phone").value;
    const password = document.getElementById("reg-password").value;
    try {
        const response = await fetch(`${API_URL}/register`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `email=${encodeURIComponent(email)}&phone=${encodeURIComponent(phone)}&password=${encodeURIComponent(password)}`
        });
        const data = await response.json();
        if (response.ok) {
            document.getElementById("reg-success").textContent = language === "ru" ? `Код отправлен: ${data.verification_code}` : `Code sent: ${data.verification_code}`;
            document.getElementById("reg-error").textContent = "";
        } else {
            document.getElementById("reg-error").textContent = data.detail;
            document.getElementById("reg-success").textContent = "";
        }
    } catch (error) {
        document.getElementById("reg-error").textContent = language === "ru" ? `Ошибка: ${error.message}` : `Error: ${error.message}`;
    }
}

async function verify() {
    const email = document.getElementById("verify-email").value;
    const code = document.getElementById("verify-code").value;
    const passport = document.getElementById("passport-upload").files[0];
    const formData = new FormData();
    formData.append("email", email);
    formData.append("code", code);
    if (passport) formData.append("passport", passport);
    try {
        const response = await fetch(`${API_URL}/verify`, {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        if (response.ok) {
            document.getElementById("verify-success").textContent = language === "ru" ? "Верификация успешна" : "Verification successful";
            document.getElementById("verify-error").textContent = "";
        } else {
            document.getElementById("verify-error").textContent = data.detail;
            document.getElementById("verify-success").textContent = "";
        }
    } catch (error) {
        document.getElementById("verify-error").textContent = language === "ru" ? `Ошибка: ${error.message}` : `Error: ${error.message}`;
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
            isAdmin = data.is_admin;
            localStorage.setItem("token", token);
            localStorage.setItem("userId", userId);
            localStorage.setItem("isAdmin", isAdmin);
            document.getElementById("login-success").textContent = language === "ru" ? "Вход успешен" : "Login successful";
            document.getElementById("login-error").textContent = "";
            document.getElementById("auth-section").style.display = "none";
            document.getElementById("user-section").style.display = "block";
            document.getElementById("logout-link").style.display = "inline";
            document.getElementById("profile-link").style.display = "inline";
            document.getElementById("user-email").textContent = email;
            document.getElementById("user-trades").textContent = data.trades_completed;
            document.getElementById("user-balance").textContent = "0";
            if (isAdmin) {
                document.getElementById("admin-section").style.display = "block";
                fetchAdminStats();
                fetchUsers();
                fetchLargeTrades();
            }
            fetchOffers();
            fetchMyOffers();
        } else {
            document.getElementById("login-error").textContent = data.detail;
            document.getElementById("login-success").textContent = "";
        }
    } catch (error) {
        document.getElementById("login-error").textContent = language === "ru" ? `Ошибка: ${error.message}` : `Error: ${error.message}`;
    }
}

function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("userId");
    localStorage.removeItem("isAdmin");
    token = null;
    userId = null;
    isAdmin = false;
    document.getElementById("auth-section").style.display = "block";
    document.getElementById("user-section").style.display = "none";
    document.getElementById("admin-section").style.display = "none";
    document.getElementById("logout-link").style.display = "none";
    document.getElementById("profile-link").style.display = "none";
}

async function deposit() {
    const currency = document.getElementById("deposit-currency").value;
    const amount = document.getElementById("deposit-amount").value;
    try {
        const response = await fetch(`${API_URL}/deposit`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `user_id=${userId}¤cy=${currency}&amount=${amount}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            document.getElementById("deposit-success").textContent = language === "ru" ? `Баланс пополнен` : `Balance updated`;
            document.getElementById("deposit-error").textContent = "";
            document.getElementById("user-balance").textContent = data.usdt_balance;
        } else {
            document.getElementById("deposit-error").textContent = data.detail;
            document.getElementById("deposit-success").textContent = "";
        }
    } catch (error) {
        document.getElementById("deposit-error").textContent = language === "ru" ? `Ошибка: ${error.message}` : `Error: ${error.message}`;
    }
}

async function createOffer() {
    const offerType = document.getElementById("offer-type").value;
    const currency = document.getElementById("offer-currency").value;
    const amount = document.getElementById("offer-amount").value;
    const fiat = document.getElementById("offer-fiat").value;
    const fiatAmount = amount * (currency === "USDT" ? 1 : currency === "BTC" ? 70000 : 3500); // Примерный курс
    const paymentMethod = document.getElementById("offer-payment-method").value;
    const contact = document.getElementById("offer-contact").value;
    try {
        const response = await fetch(`${API_URL}/create-offer`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `user_id=${userId}&offer_type=${offerType}¤cy=${currency}&amount=${amount}&fiat=${fiat}&fiat_amount=${fiatAmount}&payment_method=${paymentMethod}&contact=${contact}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            document.getElementById("create-offer-success").textContent = language === "ru" ? "Заявка создана" : "Offer created";
            document.getElementById("create-offer-error").textContent = "";
            document.getElementById("user-balance").textContent = data.usdt_balance;
            fetchMyOffers();
            fetchOffers();
        } else {
            document.getElementById("create-offer-error").textContent = data.detail;
            document.getElementById("create-offer-success").textContent = "";
        }
    } catch (error) {
        document.getElementById("create-offer-error").textContent = language === "ru" ? `Ошибка: ${error.message}` : `Error: ${error.message}`;
    }
}

async function fetchOffers() {
    const offerType = currentTab;
    const currency = document.getElementById(`${offerType}-currency`).value;
    const fiat = document.getElementById(`${offerType}-fiat`).value;
    const paymentMethod = document.getElementById(`${offerType}-payment-method`).value;
    const amount = document.getElementById(`${offerType}-amount`).value || 0;
    try {
        const response = await fetch(`${API_URL}/offers?offer_type=${offerType === "buy" ? "sell" : "buy"}¤cy=${currency}&fiat=${fiat}&payment_method=${paymentMethod}&amount=${amount}`);
        const offers = await response.json();
        const offersList = document.getElementById(`${offerType}-offers-list`);
        offersList.innerHTML = "";
        offers.forEach(offer => {
            const offerDiv = document.createElement("div");
            offerDiv.className = "offer";
            offerDiv.innerHTML = `
                <div>
                    <p>ID: ${offer.id}</p>
                    <p>${language === "ru" ? "Валюта" : "Currency"}: ${offer.currency} (${offer.amount})</p>
                    <p>${language === "ru" ? "Фиат" : "Fiat"}: ${offer.fiat} (${offer.fiat_amount})</p>
                    <p>${language === "ru" ? "Метод оплаты" : "Payment Method"}: ${offer.payment_method}</p>
                    <p>${language === "ru" ? "Контакт" : "Contact"}: ${offer.contact}</p>
                </div>
                <button onclick="dealOffer(${offer.id})">${language === "ru" ? "Купить/Продать" : "Buy/Sell"}</button>
            `;
            offersList.appendChild(offerDiv);
        });
    } catch (error) {
        console.error(language === "ru" ? "Ошибка при загрузке заявок" : "Error fetching offers", error);
    }
}

async function filterOffers(tab) {
    currentTab = tab;
    fetchOffers();
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
                <div>
                    <p>ID: ${offer.id}</p>
                    <p>${language === "ru" ? "Тип" : "Type"}: ${offer.offer_type}</p>
                    <p>${language === "ru" ? "Валюта" : "Currency"}: ${offer.currency} (${offer.amount})</p>
                    <p>${language === "ru" ? "Фиат" : "Fiat"}: ${offer.fiat} (${offer.fiat_amount})</p>
                    <p>${language === "ru" ? "Метод оплаты" : "Payment Method"}: ${offer.payment_method}</p>
                    <p>${language === "ru" ? "Статус" : "Status"}: ${offer.status}</p>
                    <p>${language === "ru" ? "Заморожено" : "Frozen"}: ${offer.frozen_amount || 0} ${offer.currency}</p>
                </div>
                <div>
                    ${offer.status === "pending" ? `<button onclick="confirmOffer(${offer.id})">${language === "ru" ? "Подтвердить" : "Confirm"}</button>` : ""}
                    ${offer.status === "pending" || offer.status === "active" ? `<button onclick="cancelOffer(${offer.id})">${language === "ru" ? "Отменить" : "Cancel"}</button>` : ""}
                    ${offer.status === "pending" ? `<button onclick="openChat(${offer.id})">${language === "ru" ? "Чат" : "Chat"}</button>` : ""}
                    ${offer.status === "pending" ? `<button onclick="createDispute(${offer.id})">${language === "ru" ? "Открыть спор" : "Open Dispute"}</button>` : ""}
                </div>
            `;
            offersList.appendChild(offerDiv);
        });
    } catch (error) {
        console.error(language === "ru" ? "Ошибка при загрузке моих заявок" : "Error fetching my offers", error);
    }
}

async function dealOffer(offerId) {
    try {
        const response = await fetch(`${API_URL}/buy-offer`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `offer_id=${offerId}&buyer_id=${userId}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            alert(language === "ru" ? "Заявка куплена, ожидайте подтверждения" : "Offer bought, awaiting confirmation");
            fetchOffers();
            fetchMyOffers();
        } else {
            alert(data.detail);
        }
    } catch (error) {
        alert(language === "ru" ? `Ошибка: ${error.message}` : `Error: ${error.message}`);
    }
}

async function confirmOffer(offerId) {
    try {
        const response = await fetch(`${API_URL}/confirm-offer`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `offer_id=${offerId}&user_id=${userId}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            alert(language === "ru" ? "Подтверждение отправлено" : "Confirmation sent");
            document.getElementById("user-balance").textContent = data.usdt_balance;
            fetchMyOffers();
            fetchOffers();
        } else {
            alert(data.detail);
        }
    } catch (error) {
        alert(language === "ru" ? `Ошибка: ${error.message}` : `Error: ${error.message}`);
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
            alert(language === "ru" ? "Заявка отменена" : "Offer cancelled");
            fetchMyOffers();
            fetchOffers();
        } else {
            alert(data.detail);
        }
    } catch (error) {
        alert(language === "ru" ? `Ошибка: ${error.message}` : `Error: ${error.message}`);
    }
}

async function openChat(offerId) {
    currentOfferId = offerId;
    document.getElementById("chat-section").style.display = "block";
    document.getElementById("dispute-section").style.display = "block";
    fetchMessages();
    if (chatInterval) clearInterval(chatInterval);
    chatInterval = setInterval(fetchMessages, 5000);
}

async function fetchMessages() {
    try {
        const response = await fetch(`${API_URL}/get-messages?offer_id=${currentOfferId}&user_id=${userId}&token=${token}`);
        const messages = await response.json();
        const chatMessages = document.getElementById("chat-messages");
        chatMessages.innerHTML = "";
        messages.forEach(message => {
            const messageDiv = document.createElement("div");
            messageDiv.className = `chat-message ${message.user_id == userId ? "sent" : "received"}`;
            messageDiv.innerHTML = `
                <strong>${message.user_email}:</strong> ${message.text} <br>
                <small>${new Date(message.created_at).toLocaleString()}</small>
            `;
            chatMessages.appendChild(messageDiv);
        });
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (error) {
        console.error(language === "ru" ? "Ошибка при загрузке сообщений" : "Error fetching messages", error);
    }
}

async function sendMessage() {
    const text = document.getElementById("chat-input").value;
    if (!text) return;
    try {
        const response = await fetch(`${API_URL}/send-message`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `offer_id=${currentOfferId}&user_id=${userId}&text=${text}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            document.getElementById("chat-input").value = "";
            fetchMessages();
        } else {
            alert(data.detail);
        }
    } catch (error) {
        alert(language === "ru" ? `Ошибка: ${error.message}` : `Error: ${error.message}`);
    }
}

async function createDispute(offerId) {
    const screenshot = document.getElementById("dispute-screenshot")?.files[0];
    const video = document.getElementById("dispute-video")?.files[0];
    const formData = new FormData();
    formData.append("offer_id", offerId);
    formData.append("user_id", userId);
    formData.append("token", token);
    if (screenshot) formData.append("screenshot", screenshot);
    if (video) formData.append("video", video);
    try {
        const response = await fetch(`${API_URL}/create-dispute`, {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        if (response.ok) {
            alert(language === "ru" ? "Спор открыт" : "Dispute opened");
            fetchMyOffers();
        } else {
            alert(data.detail);
        }
    } catch (error) {
        alert(language === "ru" ? `Ошибка: ${error.message}` : `Error: ${error.message}`);
    }
}

async function fetchAdminStats() {
    try {
        const response = await fetch(`${API_URL}/admin-stats?token=${token}`);
        const data = await response.json();
        if (response.ok) {
            document.getElementById("admin-earnings-today").textContent = data.earnings_today.toFixed(2);
            document.getElementById("admin-earnings-total").textContent = data.earnings_total.toFixed(2);
            document.getElementById("active-users").textContent = data.active_users;
        }
    } catch (error) {
        console.error("Error fetching admin stats:", error);
    }
}

async function fetchUsers() {
    try {
        const response = await fetch(`${API_URL}/admin-users?token=${token}`);
        const users = await response.json();
        const userManagement = document.getElementById("user-management");
        userManagement.innerHTML = "";
        users.forEach(user => {
            const userDiv = document.createElement("div");
            userDiv.className = "user";
            userDiv.innerHTML = `
                <p>Email: ${user.email}</p>
                <p>Trades: ${user.trades_completed}</p>
                <p>Balance: ${user.balance} USDT</p>
                <p>Cancellations: ${user.cancellations}</p>
                <p>Blocked Until: ${user.blocked_until ? new Date(user.blocked_until).toLocaleString() : "N/A"}</p>
                <p>Verified: ${user.verified ? "Yes" : "No"}</p>
                <button onclick="blockUser(${user.id}, ${!user.blocked_until})">${user.blocked_until ? "Unblock" : "Block"}</button>
            `;
            userManagement.appendChild(userDiv);
        });
    } catch (error) {
        console.error("Error fetching users:", error);
    }
}

async function blockUser(userId, block) {
    // Здесь можно добавить эндпоинт для блокировки/разблокировки
    alert(`User ${userId} ${block ? "blocked" : "unblocked"} - functionality to be implemented`);
}

async function fetchDisputes() {
    try {
        const response = await fetch(`${API_URL}/get-disputes?user_id=${userId}&token=${token}`);
        const disputes = await response.json();
        const disputesList = document.getElementById("disputes-list");
        disputesList.innerHTML = "";
        disputes.forEach(dispute => {
            const disputeDiv = document.createElement("div");
            disputeDiv.className = "dispute";
            disputeDiv.innerHTML = `
                <p>ID: ${dispute.id}</p>
                <p>Offer ID: ${dispute.offer_id}</p>
                <p>Status: ${dispute.status}</p>
                <p>Created: ${new Date(dispute.created_at).toLocaleString()}</p>
                ${dispute.status === "open" ? `<input type="text" id="resolution-${dispute.id}" placeholder="${language === "ru" ? "Резолюция" : "Resolution"}">
                <select id="action-${dispute.id}">
                    <option value="resolve">${language === "ru" ? "Разрешить" : "Resolve"}</option>
                    <option value="cancel">${language === "ru" ? "Отменить" : "Cancel"}</option>
                </select>
                <button onclick="resolveDispute(${dispute.id})">${language === "ru" ? "Разрешить спор" : "Resolve Dispute"}</button>` : ""}
            `;
            disputesList.appendChild(disputeDiv);
        });
    } catch (error) {
        console.error("Error fetching disputes:", error);
    }
}

async function resolveDispute(disputeId) {
    const resolution = document.getElementById(`resolution-${disputeId}`).value;
    const action = document.getElementById(`action-${disputeId}`).value;
    try {
        const response = await fetch(`${API_URL}/resolve-dispute`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `dispute_id=${disputeId}&resolution=${resolution}&action=${action}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            alert(language === "ru" ? "Спор разрешён" : "Dispute resolved");
            fetchDisputes();
            fetchMyOffers();
        } else {
            alert(data.detail);
        }
    } catch (error) {
        alert(language === "ru" ? `Ошибка: ${error.message}` : `Error: ${error.message}`);
    }
}

async function fetchLargeTrades() {
    try {
        const response = await fetch(`${API_URL}/admin-stats?token=${token}`);
        const data = await response.json();
        const largeTrades = document.getElementById("large-trades");
        largeTrades.innerHTML = "";
        data.large_trades.forEach(trade => {
            const tradeDiv = document.createElement("div");
            tradeDiv.className = "trade";
            tradeDiv.innerHTML = `
                <p>ID: ${trade.id}</p>
                <p>Amount: ${trade.fiat_amount} ${trade.fiat}</p>
                <p>Date: ${new Date(trade.created_at).toLocaleString()}</p>
            `;
            largeTrades.appendChild(tradeDiv);
        });
    } catch (error) {
        console.error("Error fetching large trades:", error);
    }
}

function switchTab(tab) {
    currentTab = tab;
    document.getElementById("buy-tab").classList.remove("active");
    document.getElementById("sell-tab").classList.remove("active");
    document.getElementById("my-offers-tab").classList.remove("active");
    document.getElementById(`${tab}-tab`).classList.add("active");
    document.getElementById("buy-section").style.display = tab === "buy" ? "block" : "none";
    document.getElementById("sell-section").style.display = tab === "sell" ? "block" : "none";
    document.getElementById("my-offers-section").style.display = tab === "my-offers" ? "block" : "none";
    document.getElementById("chat-section").style.display = "none";
    if (chatInterval) clearInterval(chatInterval);
    fetchOffers();
}

function changeLanguage() {
    language = document.getElementById("language").value;
    document.querySelectorAll("[data-lang]").forEach(el => {
        const key = el.getAttribute("data-lang");
        const translations = {
            "register": { "ru": "Регистрация", "en": "Register" },
            "verify": { "ru": "Верификация", "en": "Verify" },
            "login": { "ru": "Вход", "en": "Login" },
            "welcome": { "ru": "Добро пожаловать,", "en": "Welcome," },
            "balance": { "ru": "Ваш баланс:", "en": "Your balance:" },
            "trades": { "ru": "Сделок завершено:", "en": "Trades completed:" },
            "deposit": { "ru": "Пополнить баланс", "en": "Deposit" },
            "buy-crypto": { "ru": "Купить криптовалюту", "en": "Buy Crypto" },
            "sell-crypto": { "ru": "Продать криптовалюту", "en": "Sell Crypto" },
            "create-offer": { "ru": "Создать заявку", "en": "Create Offer" },
            "my-offers": { "ru": "Мои заявки", "en": "My Offers" },
            "chat": { "ru": "Чат", "en": "Chat" },
            "admin-panel": { "ru": "Админский кабинет", "en": "Admin Panel" },
            "dispute": { "ru": "Открыть спор", "en": "Open Dispute" }
        };
        el.textContent = translations[key][language] + (el.id === "user-email" ? ` ${document.getElementById("user-email").textContent}` : "");
    });
    fetchOffers();
    fetchMyOffers();
}

function openSupport() {
    window.open("https://t.me/p2pp2p_p2p", "_blank");
}

function openProfile() {
    alert(language === "ru" ? "Профиль пока в разработке" : "Profile is under development");
}

if (isAdmin) {
    fetchDisputes();
}
