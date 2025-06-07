import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";

function TradePage() {
  const { adId } = useParams();
  const [ad, setAd] = useState(null);
  const [amount, setAmount] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    // Подгрузка инфо объявления по id (опционально)
    fetch(`http://localhost:8000/ads/${adId}`)
      .then(res => res.json())
      .then(data => setAd(data))
      .catch(() => setAd(null));
  }, [adId]);

  const handleBuy = async () => {
    if (!amount || isNaN(amount)) {
      setMessage("Введите корректную сумму");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/trades/buy", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          ad_id: parseInt(adId),
          amount: parseFloat(amount),
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(`✅ Успешно! ID сделки: ${data.trade_id}`);
      } else {
        setMessage(`❌ Ошибка: ${data.detail || "Произошла ошибка"}`);
      }
    } catch (error) {
      setMessage("❌ Сервер недоступен");
    }
  };

  return (
    <div style={{ maxWidth: 500, margin: "auto", padding: 20 }}>
      <h2>Покупка #{adId}</h2>
      {ad && (
        <div>
          <p>Продавец: {ad.owner_name}</p>
          <p>Цена: ₽{ad.price}</p>
          <p>Доступно: {ad.amount} USDT</p>
        </div>
      )}
      <input
        type="number"
        placeholder="Сумма в USDT"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
        style={{ width: "100%", padding: 10, marginTop: 10 }}
      />
      <button onClick={handleBuy} style={{ width: "100%", padding: 10, marginTop: 10 }}>
        Подтвердить покупку
      </button>
      {message && <p style={{ marginTop: 10 }}>{message}</p>}
    </div>
  );
}

export default TradePage;
