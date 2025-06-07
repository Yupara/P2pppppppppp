import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

function TradePage() {
  const { adId } = useParams();
  const navigate = useNavigate();
  const [amount, setAmount] = useState("");
  const [message, setMessage] = useState("");

  const handleBuy = () => {
    if (!amount || isNaN(amount)) {
      setMessage("Введите корректную сумму");
      return;
    }

    // Здесь будет реальный запрос на бекенд
    setMessage(`Вы отправили заявку на покупку на сумму ₽${amount} для объявления #${adId}`);
  };

  return (
    <div style={{ padding: 20, backgroundColor: "#002b26", minHeight: "100vh", color: "#fff" }}>
      <h2 style={{ color: "#90EE90" }}>Покупка у продавца #{adId}</h2>

      <div style={{ marginTop: 20 }}>
        <label>Сумма в RUB:</label>
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          style={{
            display: "block",
            padding: "10px",
            marginTop: "10px",
            width: "100%",
            maxWidth: "300px",
            backgroundColor: "#003f35",
            border: "1px solid #90EE90",
            color: "#fff",
          }}
        />
      </div>

      <button
        onClick={handleBuy}
        style={{
          marginTop: "20px",
          padding: "10px 20px",
          backgroundColor: "#90EE90",
          color: "#003300",
          border: "none",
          borderRadius: "5px",
          fontWeight: "bold",
          cursor: "pointer",
        }}
      >
        Подтвердить покупку
      </button>

      {message && <p style={{ marginTop: 20, color: "#FFD700" }}>{message}</p>}

      <button
        onClick={() => navigate(-1)}
        style={{
          marginTop: "40px",
          padding: "8px 16px",
          backgroundColor: "#444",
          color: "#fff",
          border: "none",
          borderRadius: "5px",
        }}
      >
        Назад
      </button>
    </div>
  );
}

export default TradePage;
