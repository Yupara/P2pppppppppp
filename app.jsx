import React, { useState } from "react";
import Market from "./Market";

export default function App() {
  const [tab, setTab] = useState("buy");

  return (
    <div style={{ backgroundColor: "#002b26", minHeight: "100vh", color: "white", fontFamily: "Arial, sans-serif" }}>
      <header style={{ padding: 20, textAlign: "center", color: "#90EE90" }}>
        <h1>P2P Платформа Bybit</h1>
      </header>

      <nav style={{ display: "flex", justifyContent: "center", backgroundColor: "#003f35", padding: 10 }}>
        <button
          onClick={() => setTab("buy")}
          style={{
            backgroundColor: "transparent",
            color: tab === "buy" ? "#90EE90" : "rgba(255, 255, 255, 0.8)",
            border: "none",
            padding: "10px 20px",
            fontSize: 16,
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          Покупка
        </button>
        <button
          onClick={() => setTab("sell")}
          style={{
            backgroundColor: "transparent",
            color: tab === "sell" ? "#90EE90" : "rgba(255, 255, 255, 0.8)",
            border: "none",
            padding: "10px 20px",
            fontSize: 16,
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          Продажа
        </button>
      </nav>

      <main style={{ padding: 20 }}>
        <Market type={tab} />
      </main>
    </div>
  );
}
