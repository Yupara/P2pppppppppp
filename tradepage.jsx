import React from "react";
import { useParams, useNavigate } from "react-router-dom";

function TradePage() {
  const { adId } = useParams();
  const navigate = useNavigate();

  return (
    <div style={{ padding: 20, color: "#90EE90", backgroundColor: "#002b26", minHeight: "100vh" }}>
      <h1>Детали сделки {adId}</h1>
      {/* Тут можно будет добавить форму сделки и чат */}
      <button onClick={() => navigate(-1)} style={{ marginTop: 20, padding: "10px 20px" }}>
        Назад
      </button>
    </div>
  );
}

export default TradePage;
