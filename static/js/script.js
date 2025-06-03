const API_URL = "https://p2pppppppppp-production.up.railway.app";
let token = localStorage.getItem("token");
let userId = localStorage.getItem("userId");
let language = localStorage.getItem("language") || "ru";

const translations = {
    ru: {
        welcome: "Добро пожаловать",
        logout: "Выйти",
        announcements: "Объявления",
        profile: "Профиль",
        support: "Поддержка",
        registration: "Регистрация",
        verification: "Верификация",
        login: "Вход",
        email: "Email",
        phone: "Телефон",
        password: "Пароль",
        register: "Зарегистрироваться",
        verify: "Верифицировать",
        code: "Код",
        loginBtn: "Войти",
        balance: "Баланс",
        tradesCompleted: "Сделок завершено",
        cancellations: "Отмен сделок",
        referralCode: "Реферальный код",
        referralEarnings: "Реферальный доход",
        withdrawReferral: "Вывести реферальный доход",
        identityVerification: "Верификация личности",
        uploadPassport: "Загрузить паспорт",
        deposit: "Пополнить",
        amount: "Сумма",
        createOffer: "Создать объявление",
        sellCurrency: "Валюта продажи",
        buyCurrency: "Валюта покупки",
        paymentMethod: "Метод оплаты",
        contact: "Контакт",
        myOffers: "Мои объявления",
        filters: "Фильтры",
        selectSellCurrency: "Выберите валюту продажи",
        selectBuyCurrency: "Выберите валюту покупки",
        selectPaymentMethod: "Выберите метод оплаты",
        minAmount: "Мин. сумма",
        maxAmount: "Макс. сумма",
        applyFilters: "Применить фильтры",
        supportMessage: "Напишите ваш запрос",
        send: "Отправить",
        adminPanel: "Админ-панель",
        totalEarnings: "Общий доход",
        withdrawEarnings: "Вывести доход",
        activeUsers: "Активные пользователи",
        disputes: "Споры",
        manageUsers: "Управление пользователями",
        userId: "ID пользователя",
        block: "Заблокировать",
        unblock: "Разблокировать",
        buy: "Купить",
        confirmPayment: "Подтвердить оплату",
        openDispute: "Открыть спор",
        sendMessage: "Отправить сообщение",
        chat: "Чат"
    },
    en: {
        welcome: "Welcome",
        logout: "Logout",
        announcements: "Announcements",
        profile: "Profile",
        support: "Support",
        registration: "Registration",
        verification: "Verification",
        login: "Login",
        email: "Email",
        phone: "Phone",
        password: "Password",
        register: "Register",
        verify: "Verify",
        code: "Code",
        loginBtn: "Login",
        balance: "Balance",
        tradesCompleted: "Trades Completed",
        cancellations: "Cancellations",
        referralCode: "Referral Code",
        referralEarnings: "Referral Earnings",
        withdrawReferral: "Withdraw Referral Earnings",
        identityVerification: "Identity Verification",
        uploadPassport: "Upload Passport",
        deposit: "Deposit",
        amount: "Amount",
        createOffer: "Create Offer",
        sellCurrency: "Sell Currency",
        buyCurrency: "Buy Currency",
        paymentMethod: "Payment Method",
        contact: "Contact",
        myOffers: "My Offers",
        filters: "Filters",
        selectSellCurrency: "Select Sell Currency",
        selectBuyCurrency: "Select Buy Currency",
        selectPaymentMethod: "Select Payment Method",
        minAmount: "Min Amount",
        maxAmount: "Max Amount",
        applyFilters: "Apply Filters",
        supportMessage: "Write your request",
        send: "Send",
        adminPanel: "Admin Panel",
        totalEarnings: "Total Earnings",
        withdrawEarnings: "Withdraw Earnings",
        activeUsers: "Active Users",
        disputes: "Disputes",
        manageUsers: "Manage Users",
        userId: "User ID",
        block: "Block",
        unblock: "Unblock",
        buy: "Buy",
        confirmPayment: "Confirm Payment",
        openDispute: "Open Dispute",
        sendMessage: "Send Message",
        chat: "Chat"
    }
};

function toggleLanguage() {
    language = language === "ru" ? "en" : "ru";
    localStorage.setItem("language", language);
    updateLanguage();
}

function updateLanguage() {
    document.querySelectorAll("[data-translate]").forEach(el => {
        const key = el.getAttribute("data-translate");
        el.textContent = translations[language][key];
    });
    document.querySelectorAll("input, button").forEach(el => {
        if (el.placeholder) {
            const key = el.getAttribute("data-translate-placeholder");
            if (key) el.placeholder = translations[language][key];
        }
        if (el.tagName === "BUTTON") {
            const key = el.getAttribute("data-translate");
            if (key) el.textContent = translations[language][key];
        }
    });
}

if (token && userId) {
    document.getElementById("auth-section").style.display = "none";
    document.getElementById("offers-section").style.display = "block";
    document.getElementById("logout-btn").style.display = "inline-block";
    fetchUserProfile();
    fetchOffers();
    fetchMyOffers();
    if (userId === "1") {
        document.getElementById("admin-section").style.display = "block";
        fetchAdminData();
    }
}

function showSection(sectionId) {
    document.querySelectorAll(".container > div").forEach(section => {
        section.style.display = "none";
    });
    document.getElementById(sectionId).style.display = "block";
}

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
            document.getElementById("reg-success").textContent = `Код отправлен: ${data.verification_code}`;
            document.getElementById("reg-error").textContent = "";
        } else {
            document.getElementById("reg-error").textContent = data.detail;
            document.getElementById("reg-success").textContent = "";
        }
    } catch (error) {
        document.getElementById("reg-error").textContent = "Ошибка: " + error.message;
    }
}

async function verify() {
    const email = document.getElementById("verify-email").value;
    const code = document.getElementByIdverify-code").value;
    try {
        const response = await fetch(`${API_URL}/verify`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `email=${encodeURIComponent(email)}`
        });
        const data = await response.json();
        if (response.ok) {
            document.getElementById("verify-success").textContent = translations[language].verifySuccess;
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
            document.getElementById("login-success").textContent = translations[language].loginSuccess;
            document.getElementById("login-error").textContent = "";
            document.getElementById("auth-section").style.display = "none";
            document.getElementById("offers-section").style.display = "block";
            document.getElementById("logout-btn").style.display = "inline-block";
            fetchUserProfile();
            fetchOffers();
            fetchMyOffers();
            if (userId === "1") {
                document.getElementById("admin-section").style.display = "block";
                fetchAdminData();
            }
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
    document.getElementById("offers-section").style.display = "none";
    document.getElementById("profile-section").style.display = "none";
    document.getElementById("support-section").style.display = "none";
    document.getElementById("admin-section").style.display = "none";
    document.getElementById("logout-btn").style.display = "none";
}

async function fetchUserProfile() {
    try {
        const response = await fetch(`${API_URL}/profile?user_id=${userId}&token=${token}`);
        const data = await response.json();
        if (response.ok) {
            document.getElementById("user-email").textContent = data.email;
            document.getElementById("user-balance").textContent = data.balance;
            document.getElementById("user-trades").textContent = data.trades_completed;
            document.getElementById("user-cancellations").textContent = data.cancellations;
            document.getElementById("user-referral-code").textContent = data.referral_code;
            document.getElementById("user-referral-earnings").textContent = data.referral_earnings;
            document.getElementById("passport-status").textContent = data.passport_verified ? "Паспорт верифицирован" : "Паспорт не загружен";
        } else {
            alert("Ошибка: " + data.detail);
        }
    } catch (error) {
        alert("Ошибка: " + error.message);
    }
}

async function uploadPassport() {
    const passportFile = document.getElementById("passport-upload").files[0];
    const formData = new FormData();
    formData.append("passport", passportFile);
    try {
        const response = await fetch(`${API_URL}/upload-passport?user_id=${userId}&token=${token}`, {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        if (response.ok) {
            document.getElementById("passport-status").textContent = "Паспорт загружен, ожидает проверки";
        } else {
            alert("Ошибка: " + data.detail);
        }
    } catch (error) {
        alert("Ошибка: " + error.message);
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
            document.getElementById("deposit-success").textContent = `Баланс пополнен: ${data.new_balance}`;
            document.getElementById("deposit-error").textContent = "";
            document.getElementById("user-balance").textContent = data.new_balance;
        } else {
            document.getElementById("deposit-error").textContent = data.detail;
            document.getElementById("deposit-success").textContent = "";
        }
    } catch (error) {
        document.getElementById("deposit-error").textContent = error.message;
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
            body: `user_id=${userId}&sell_currency=${sellCurrency}&sell_amount=${sellAmount}&buy_currency=${buyCurrency}&payment_method=${paymentMethod}&contact=${contact}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            document.getElementById("create-offer-success").textContent = "Объявление создано";
            document.getElementById("create-offer-error").textContent = "";
            document.getElementById("user-balance").textContent = data.seller_balance;
            fetchOffers();
            fetchMyOffers();
        } else {
            document.getElementById("create-offer-error").textContent = data.detail;
            document.getElementById("create-offer-success").textContent = "";
        }
    } catch (error) {
        document.getElementById("create-offer-error").textContent = error.message;
    }
}

async function fetchOffers() {
    const sellCurrency = document.getElementById("filter-sell-currency").value;
    const buyCurrency = document.getElementById("filter-buy-currency").value;
    const paymentMethod = document.getElementById("filter-payment-method").value;
    const minAmount = document.getElementById("filter-min-amount").value;
    const maxAmount = document.getElementById("filter-max-amount").value;
    let query = new URLSearchParams();
    if (sellCurrency) query.append("sell_currency", sellCurrency);
    if (buyCurrency) query.append("buy_currency", buyCurrency);
    if (paymentMethod) query.append("payment_method", paymentMethod);
    if (minAmount) query.append("min_amount", minAmount);
    if (maxAmount) query.append("max_amount", maxAmount);

    try {
        const response = await fetch(`${API_URL}/offers?${query}`);
        const offers = await response.json();
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
        console.error("Ошибка: ", error);
    }
}

async function fetchMyOffers() {
    try {
        const response = await fetch(`${API_URL}/my-offers?user_id=${userId}&token=${token}`);
        const offers = await response.json();
        const myOffersList = document.getElementById("my-offers-list");
        myOffersList.innerHTML = "";
        offers.forEach(offer => {
            const offerDiv = document.createElement("div");
            offerDiv.className = "offer";
            offerDiv.innerHTML = `
                <p>ID: ${offer.id}</p>
                <p>Продажа: ${offer.sell_amount} ${offer.sell_currency}</p>
                <p>Покупка: ${offer.buy_currency}</p>
                <p>Метод оплаты: ${offer.payment_method}</p>
                <p>Контакт: ${offer.contact}</p>
                <p>Статус: ${offer.status}</p>
                ${offer.status === "in-progress" ? `
                    <button onclick="confirmPayment(${offer.id})">Подтвердить оплату</button>
                    <button onclick="openDispute(${offer.id})">Открыть спор</button>
                    <div id="chat-${offer.id}">
                        <h3>Чат</h3>
                        <div id="messages-${offer.id}"></div>
                        <input type="text" id="message-input-${offer.id}" placeholder="Сообщение">
                        <button onclick="sendMessage(${offer.id})">Отправить</button>
                    </div>
                ` : ""}
                <button onclick="deleteOffer(${offer.id})">Удалить</button>
            `;
            myOffersList.appendChild(offerDiv);
            if (offer.status === "in-progress") fetchMessages(offer.id);
        });
    } catch (error) {
        console.error("Ошибка: ", error);
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
            alert("Заявка куплена");
            fetchOffers();
            fetchMyOffers();
        } else {
            alert("Ошибка: ", data.detail);
        }
    } catch (error) {
        alert("Ошибка: ", error.message);
    }
}

async function confirmPayment(offerId) {
    try {
        const response = await fetch(`${API_URL}/confirm-offer`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `offer_id=${offerId}&user_id=${userId}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            alert("Сделка завершена");
            fetchMyOffers();
            fetchUserProfile();
        } else {
            alert("Ошибка: ", data.detail);
        }
    } catch (error) {
        alert("Ошибка: ", error.message);
    }
}

async function openDispute(offerId) {
    const screenshot = prompt("Введите ссылку на скриншот");
    const video = prompt("Введите ссылку на видео (опционально)");
    try {
        const response = await fetch(`${API_URL}/create-dispute`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `offer_id=${offerId}&user_id=${userId}&screenshot=${screenshot}&video=${video}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            alert("Спор создан");
            fetchMyOffers();
        } else {
            alert("Ошибка: ", data.detail);
        }
    } catch (error) {
        alert("Ошибка: ", error.message);
    }
}

async function sendMessage(offerId) {
    const text = document.getElementById(`message-input-${offerId}`).value;
    try {
        const response = await fetch(`${API_URL}/send-message`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `offer_id=${offerId}&user_id=${userId}&text=${text}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            fetchMessages(offerId);
            document.getElementById(`message-input-${offerId}`).value = "";
        } else {
            alert("Ошибка: ", data.detail);
        }
    } catch (error) {
        alert("Ошибка: ", error.message);
    }
}

async function fetchMessages(offerId) {
    try {
        const response = await fetch(`${API_URL}/get-messages?offer_id=${offerId}&user_id=${userId}&token=${token}`);
        const messages = await response.json();
        const messagesDiv = document.getElementById(`messages-${offerId}`);
        messagesDiv.innerHTML = "";
        messages.forEach(msg => {
            const messageDiv = document.createElement("div");
            messageDiv.textContent = `${msg.user_id}: ${msg.text} (${new Date(msg.created_at).toLocaleString()})`;
            messagesDiv.appendChild(messageDiv);
        });
    } catch (error) {
        console.error("Ошибка: ", error);
    }
}

async function deleteOffer(offerId) {
    try {
        const response = await fetch(`${API_URL}/delete-offer`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `offer_id=${offerId}&user_id=${userId}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            alert("Объявление удалено");
            fetchMyOffers();
            fetchOffers();
        } else {
            alert("Ошибка: ", data.detail);
        }
    } catch (error) {
        alert("Ошибка: ", error.message);
    }
}

async function withdrawReferralEarnings() {
    try {
        const response = await fetch(`${API_URL}/withdraw-referral`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `user_id=${userId}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            alert("Реферальный доход выведен");
            fetchUserProfile();
        } else {
            alert("Ошибка: ", data.detail);
        }
    } catch (error) {
        alert("Ошибка: ", error.message);
    }
}

async function sendSupportMessage() {
    const message = document.getElementById("support-message").value;
    try {
        const response = await fetch(`${API_URL}/support-message`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `user_id=${userId}&message=${message}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            document.getElementById("support-success").textContent = "Сообщение отправлено";
            const chatDiv = document.getElementById("support-chat");
            chatDiv.innerHTML += `<p>Вы: ${message}</p>`;
            if (message.toLowerCase().includes("оператор")) {
                chatDiv.innerHTML += `<p>Система: Администратор уведомлен, ожидайте ответа.</p>`;
            } else {
                chatDiv.innerHTML += `<p>Бот: Ваш запрос принят, мы поможем вам в ближайшее время.</p>`;
            }
        } else {
            alert("Ошибка: ", data.detail);
        }
    } catch (error) {
        alert("Ошибка: ", error.message);
    }
}

async function fetchAdminData() {
    try {
        const response = await fetch(`${API_URL}/admin-data?user_id=${userId}&token=${token}`);
        const data = await response.json();
        if (response.ok) {
            document.getElementById("admin-total-earnings").textContent = data.total_earnings;
            const usersList = document.getElementById("admin-users-list");
            usersList.innerHTML = "";
            data.users.forEach(user => {
                const userDiv = document.createElement("div");
                userDiv.textContent = `ID: ${user.id}, Email: ${user.email}, Сделок: ${user.trades_completed}, Отмен: ${user.cancellations}, Активен: ${!user.blocked}`;
                usersList.appendChild(userDiv);
            });
            const disputesList = document.getElementById("admin-disputes-list");
            disputesList.innerHTML = "";
            data.disputes.forEach(dispute => {
                const disputeDiv = document.createElement("div");
                disputeDiv.innerHTML = `
                    <p>ID: ${dispute.id}, Заявка: ${dispute.offer_id}, Статус: ${dispute.status}</p>
                    <p>Скриншот: <a href="${dispute.screenshot}" target="_blank">Посмотреть</a></p>
                    <p>Видео: ${dispute.video ? `<a href="${dispute.video}" target="_blank">Посмотреть</a>` : "Нет"}</p>
                    <button onclick="resolveDispute(${dispute.id}, 'resolve')">Решить</button>
                    <button onclick="resolveDispute(${dispute.id}, 'cancel')">Отменить</button>
                `;
                disputesList.appendChild(disputeDiv);
            });
        } else {
            alert("Ошибка: ", data.detail);
        }
    } catch (error) {
        alert("Ошибка: ", error.message);
    }
}

async function resolveDispute(disputeId, action) {
    const resolution = prompt("Введите решение");
    try {
        const response = await fetch(`${API_URL}/resolve-dispute`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `dispute_id=${disputeId}&admin_id=${userId}&resolution=${resolution}&action=${action}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            alert("Спор решён");
            fetchAdminData();
        } else {
            alert("Ошибка: ", data.error);
        }
    } catch (error) {
        alert("Ошибка: ", error.message);
    }
}

async function withdrawEarnings() {
    try {
        const response = await fetch(`${API_URL}/withdraw-earnings`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `user_id=${userId}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            alert("Доход выведен");
            fetchAdminData();
        } else {
            alert("Ошибка: ", data.detail);
        }
    } catch (error) {
        alert("Ошибка: ", error.message);
    }
}

async function blockUser() {
    const targetUserId = document.getElementById("admin-user-id").value;
    try {
        const response = await fetch(`${API_URL}/block-user`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `user_id=${targetUserId}&admin_id=${userId}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            alert("Пользователь заблокирован");
            fetchAdminData();
        } else {
            alert("Ошибка: ", data.detail);
        }
    } catch (error) {
        alert("Ошибка: ", error.message);
    }
}

async function unblockUser() {
    const targetUserId = document.getElementById("admin-user-id").value;
    try {
        const response = await fetch(`${API_URL}/unblock-user`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `user_id=${targetUserId}&admin_id=${userId}&token=${token}`
        });
        const data = await response.json();
        if (response.ok) {
            alert("Пользователь разблокирован");
            fetchAdminData();
        } else {
            alert("Ошибка: ", data.detail);
        }
    } catch (error) {
        alert("Ошибка: ", error.message);
    }
}

updateLanguage();
