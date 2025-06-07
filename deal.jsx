import React, { useState } from "react";

export default function Deal({ deal, goBack }) {
    const [amount, setAmount] = useState(deal.amount);
    const [status, setStatus] = useState("init");
    const [dealData, setDealData] = useState(null);
    const [error, setError] = useState("");

    const startDeal = () => {
        if (!amount || amount <= 0 || amount > deal.ad.available) {
            setError("Введите корректную сумму");
            return;
        }
        setError("");
        fetch("http://localhost:8000/deals", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ad_id: deal.ad.id, user: deal.user, amount: parseFloat(amount) })
        }).then(res => {
            if (!res.ok) throw new Error("Ошибка создания сделки");
            return res.json();
        }).then(data => {
            setDealData(data);
            setStatus("created");
        }).catch(e => setError(e.message));
    };

    if (status === "init") {
        return (
            <div style={{ backgroundColor: "#002b26", padding: 20, borderRadius: 10, color: "white" }}>
                <button onClick={goBack} style={{ marginBottom: 20, cursor: "pointer" }}>← Назад</button>
                <h2>Создать сделку</h2>
                <p><b>{deal.ad.user}</b> предлагает {deal.ad.coin} по цене ₽{deal.ad.price.toFixed(2)}</p>
                <p>Доступно: {deal.ad.available}</p>
                <p>Лимиты: {deal.ad.limits}</p>
                <input
                    type="number"
                    placeholder="Введите сумму"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    style={{ padding: 10, width: "100%", marginBottom: 10 }}
                />
                <button onClick={startDeal} style={{ padding: 10, width: "100%", backgroundColor: "#90EE90", color: "#003300", border: "none", borderRadius: 5, cursor: "pointer" }}>
                    Начать сделку
                </button>
                {error && <p style={{ color: "red" }}>{error}</p>}
            </div>
        );
    }

    if (status === "created" && dealData) {
        return (
            <div style={{ backgroundColor: "#002b26", padding: 20, borderRadius: 10, color: "white" }}>
                <button onClick={goBack} style={{ marginBottom: 20, cursor: "pointer" }}>← Назад</button>
                <h2>Сделка создана</h2>
                <p>Сделка ID: {dealData.id}</p>
                <p>Сумма: {dealData.amount}</p>
                <p>Статус: {dealData.status}</p>
                <p>Ожидайте инструкции для оплаты...</p>
            </div>
        );
    }

    return null;
}
