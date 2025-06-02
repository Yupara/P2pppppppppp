const functions = require('firebase-functions');
const admin = require('firebase-admin');
admin.initializeApp();

exports.sendVerificationCode = functions.https.onCall(async (data, context) => {
    const { email, phone } = data;
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    // Симуляция отправки email (замени на реальную службу, например SendGrid)
    console.log(`Код подтверждения ${code} отправлен на ${email} и ${phone}`);
    return { code }; // Для теста возвращаем код напрямую
});

exports.notifyAdmin = functions.https.onCall(async (data, context) => {
    const { userId, message } = data;
    if (message.toLowerCase().includes('оператор')) {
        // Отправка уведомления в Telegram @p2pp2p_p2p
        const telegramBotToken = 'YOUR_TELEGRAM_BOT_TOKEN';
        const chatId = 'YOUR_CHAT_ID';
        const url = `https://api.telegram.org/bot${telegramBotToken}/sendMessage?chat_id=${chatId}&text=Запрос оператора от ${userId}: ${message}`;
        await fetch(url);
    }
    return { success: true };
});

exports.sendNotification = functions.https.onCall(async (data, context) => {
    const { userId, offerId, status } = data;
    const user = await admin.firestore().collection('users').doc(userId).get();
    const phone = user.data().phone;
    // Симуляция SMS (замени на Twilio или аналог)
    console.log(`SMS на ${phone}: Заявка ${offerId} ${status === 'completed' ? 'завершена' : 'начата'}!`);
    return { success: true };
});

exports.getTotalCommission = functions.https.onCall(async (data, context) => {
    const snapshot = await admin.firestore().collection('transactions').get();
    let total = 0;
    snapshot.forEach(doc => {
        const tx = doc.data();
        if (tx.commission) total += tx.commission;
    });
    return total;
});

exports.withdrawCommission = functions.https.onCall(async (data, context) => {
    const { wallet } = data;
    const total = await getTotalCommission();
    // Симуляция вывода
    console.log(`Вывод ${total} USDT на ${wallet}`);
    return { success: true };
});

exports.dailyEarnings = functions.pubsub.schedule('0 0 * * *').onRun(async (context) => {
    const total = await getTotalCommission();
    const telegramBotToken = 'YOUR_TELEGRAM_BOT_TOKEN';
    const chatId = 'YOUR_CHAT_ID';
    const url = `https://api.telegram.org/bot${telegramBotToken}/sendMessage?chat_id=${chatId}&text=Заработано сегодня: ${total.toFixed(2)} USDT`;
    await fetch(url);
});

async function getTotalCommission() {
    const snapshot = await admin.firestore().collection('transactions').get();
    let total = 0;
    snapshot.forEach(doc => {
        const tx = doc.data();
        if (tx.commission) total += tx.commission;
    });
    return total;
}
