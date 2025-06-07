import React, { useEffect, useState } from "react";

function MyTrades() {
  const [trades, setTrades] = useState([]);

  useEffect(() => {
    const token = localStorage.getItem("token");

    fetch("http://localhost:8000/trades/my", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => res.json())
      .then((data) => setTrades(data))
      .catch((err) => console.error("Ошибка загрузки сделок", err));
  }, []);

  return (
    <div style={{ maxWidth: 600, margin: "auto", padding: 20 }}>
      <h2>Мои сделки</h2>
      {trades.length === 0 && <p>Нет сделок</p>}
      {trades.map((trade) => (
        <div key={trade.trade_id} style={{ padding: 10, border: "1px solid #ccc", marginBottom: 10 }}>
          <p><strong>ID сделки:</strong> {trade.trade_id}</p>
          <p><strong>ID объявления:</strong> {trade.ad_id}</p>
          <p><strong>Сумма:</strong> {trade.amount} USDT</p>
        </div>
      ))}
    </div>
  );
}

export default MyTrades;
