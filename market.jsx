import React, { useState } from "react";

const sampleAds = {
  buy: [
    {
      id: 1,
      username: "Savak",
      orders: 40,
      completion: 90,
      price: 70.96,
      amount: 304.7685,
      limits: "500 – 500 000 RUB",
      payments: ["SBP", "Пиметы"],
      online: true,
    },
    {
      id: 2,
      username: "Ищу_Партнеров",
      orders: 15,
      completion: 10,
      price: 71.03,
      amount: 128.8821,
      limits: "500 – 500 000 RUB",
      payments: ["SBP", "Овореол"],
      online: false,
    },
  ],
  sell: [
    {
      id: 3,
      username: "TraderX",
      orders: 22,
      completion: 80,
      price: 71.50,
      amount: 150.0,
      limits: "1000 – 400 000 RUB",
      payments: ["Transfer", "QIWI"],
      online: true,
    },
    {
      id: 4,
      username: "CryptoKing",
      orders: 10,
      completion: 95,
      price: 70.80,
      amount: 200.0,
      limits: "200 – 300 000 RUB",
      payments: ["Cash", "SBP"],
      online: false,
    },
  ],
};

export default function Market({ type }) {
  const [filters, setFilters] = useState({
    coin: "USDT",
    amount: "",
    payment: "all",
  });

  const handleFilterChange = (e) => {
    setFilters((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const filteredAds = sampleAds[type].filter((ad) => {
    if (filters.payment !== "all" && !ad.payments.map(p => p.toLowerCase()).includes(filters.payment.toLowerCase())) {
      return false;
    }
    if (filters.amount && Number(filters.amount) > ad.amount) {
      return false;
    }
    if (filters.coin !== "USDT") {
      // For demo, all ads USDT only, skip filtering by coin
    }
    return true;
  });

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "center", gap: 10, marginBottom: 20 }}>
        <select name="coin" value={filters.coin} onChange={handleFilterChange} style={selectStyle}>
          <option value="USDT">USDT</option>
          <option value="BTC">BTC</option>
          <option value="ETH">ETH</option>
        </select>
        <select name="amount" value={filters.amount} onChange={handleFilterChange} style={selectStyle}>
          <option value="">Сумма</option>
          <option value="1000">1000</option>
          <option value="5000">5000</option>
        </select>
        <select name="payment" value={filters.payment} onChange={handleFilterChange} style={selectStyle}>
          <option value="all">Все способы оплаты</option>
          <option value="sbp">SBP</option>
          <option value="transfer">Банковский перевод</option>
          <option value="cash">Наличные</option>
          <option value="qiwi">QIWI</option>
        </select>
      </div>

      <div style={{ maxWidth: 800, margin: "auto" }}>
        {filteredAds.length === 0 ? (
          <p style={{ textAlign: "center", color: "#90EE90" }}>Объявления не найдены</p>
        ) : (
          filteredAds.map((ad) => (
            <div key={ad.id} style={cardStyle}>
              <div style={{ display: "flex", alignItems: "center", gap: 15 }}>
                <div
                  style={{
                    ...statusDotStyle,
                    backgroundColor: ad.online ? "#90EE90" : "#FF4500",
                  }}
                  title={ad.online ? "Онлайн" : "Оффлайн"}
                />
                <img
                  src={`https://ui-avatars.com/api/?name=${ad.username}&background=003f35&color=90EE90`}
                  alt={ad.username}
                  style={{ borderRadius: "50%", width: 50, height: 50 }}
                />
                <div>
                  <h3 style={{ margin: 0, color: "#FFD700" }}>{ad.username}</h3>
                  <p style={{ margin: 0, fontSize: 14 }}>
                    {ad.orders} ордеров | {ad.completion}% выполнено
                  </p>
                </div>
              </div>
              <div style={{ textAlign: "left", marginLeft: 20, flex: 1 }}>
                <p>Цена: ₽{ad.price.toFixed(2)}</p>
                <p>Количество: {ad.amount.toFixed(4)} USDT</p>
                <p>Лимиты: {ad.limits}</p>
                <p>Способы оплаты: {ad.payments.join(", ")}</p>
              </div>
              <div style={{ textAlign: "right" }}>
                <button
                  style={buttonStyle}
                  onClick={() => alert(`Вы выбрали объявление от ${ad.username}`)}
                >
                  {type === "buy" ? "Купить" : "Продать"}
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

const selectStyle = {
  padding: 10,
  borderRadius: 5,
  border: "1px solid #90EE90",
  backgroundColor: "#003f35",
  color: "white",
  fontSize: 16,
  fontWeight: "bold",
};

const cardStyle = {
  display: "flex",
  alignItems: "center",
  backgroundColor: "#003f35",
  borderRadius: 10,
  padding: 20,
  marginBottom: 20,
  boxShadow: "0 4px 8px rgba(0,0,0,0.2)",
};

const statusDotStyle = {
  width: 12,
  height: 12,
  borderRadius: "50%",
};

const buttonStyle = {
  backgroundColor: "#90EE90",
  color: "#003300",
  border: "none",
  borderRadius: 5,
  padding: "10px 20px",
  fontWeight: "bold",
  fontSize: 16,
  cursor: "pointer",
};
