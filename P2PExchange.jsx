import React, { useState } from "react";

const darkGreen = "#064420";
const lightGreen = "#1e7e34";
const bgColor = "#0a2a12";
const textColor = "#d4f1d4";

function P2PExchange() {
  const [ads, setAds] = useState([
    { id: 1, type: "Buy", crypto: "BTC", fiat: "USD", price: 29000, amount: 0.5, user: "Alice" },
    { id: 2, type: "Sell", crypto: "ETH", fiat: "USD", price: 1900, amount: 1.2, user: "Bob" },
  ]);

  const [form, setForm] = useState({
    type: "Buy",
    crypto: "BTC",
    fiat: "USD",
    price: "",
    amount: "",
  });

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleCreateAd = () => {
    if (!form.price || !form.amount) return alert("Fill all fields");
    const newAd = {
      id: ads.length + 1,
      ...form,
      price: parseFloat(form.price),
      amount: parseFloat(form.amount),
      user: "You",
    };
    setAds(prev => [newAd, ...prev]);
    setForm({ type: "Buy", crypto: "BTC", fiat: "USD", price: "", amount: "" });
  };

  return (
    <div style={{ backgroundColor: bgColor, minHeight: "100vh", padding: 20, color: textColor, fontFamily: "Arial, sans-serif" }}>
      <h1 style={{ textAlign: "center", marginBottom: 30 }}>P2P Crypto Exchange</h1>

      <div style={{ maxWidth: 600, margin: "auto", backgroundColor: darkGreen, borderRadius: 8, padding: 20, boxShadow: `0 0 10px ${lightGreen}` }}>
        <h2>Create New Order</h2>
        <div style={{ display: "flex", gap: 10, marginBottom: 15 }}>
          <select name="type" value={form.type} onChange={handleChange} style={selectStyle}>
            <option>Buy</option>
            <option>Sell</option>
          </select>
          <select name="crypto" value={form.crypto} onChange={handleChange} style={selectStyle}>
            <option>BTC</option>
            <option>ETH</option>
            <option>USDT</option>
            <option>BNB</option>
          </select>
          <select name="fiat" value={form.fiat} onChange={handleChange} style={selectStyle}>
            <option>USD</option>
            <option>EUR</option>
            <option>RUB</option>
            <option>UAH</option>
          </select>
        </div>

        <input
          type="number"
          name="price"
          placeholder="Price per coin"
          value={form.price}
          onChange={handleChange}
          style={inputStyle}
        />
        <input
          type="number"
          name="amount"
          placeholder="Amount"
          value={form.amount}
          onChange={handleChange}
          style={inputStyle}
        />

        <button onClick={handleCreateAd} style={buttonStyle}>Create Order</button>
      </div>

      <h2 style={{ textAlign: "center", margin: "40px 0 20px" }}>Open Orders</h2>
      <div style={{ maxWidth: 700, margin: "auto" }}>
        {ads.length === 0 && <p>No orders yet</p>}
        {ads.map(ad => (
          <div key={ad.id} style={{ backgroundColor: darkGreen, marginBottom: 10, padding: 15, borderRadius: 6, boxShadow: `0 0 5px ${lightGreen}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <strong style={{ color: ad.type === "Buy" ? "#6fdb6f" : "#db6f6f" }}>{ad.type}</strong> {ad.crypto} / {ad.fiat}<br />
              Price: {ad.price} {ad.fiat}<br />
              Amount: {ad.amount} {ad.crypto}
            </div>
            <div style={{ fontStyle: "italic", fontSize: 12, color: "#aaa" }}>
              User: {ad.user}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const selectStyle = {
  flex: 1,
  padding: 8,
  borderRadius: 4,
  border: "1px solid #4CAF50",
  backgroundColor: "#0a2a12",
  color: "#d4f1d4",
};

const inputStyle = {
  width: "100%",
  padding: 10,
  marginBottom: 15,
  borderRadius: 4,
  border: "1px solid #4CAF50",
  backgroundColor: "#0a2a12",
  color: "#d4f1d4",
};

const buttonStyle = {
  width: "100%",
  padding: 12,
  backgroundColor: "#1e7e34",
  border: "none",
  borderRadius: 6,
  color: "#d4f1d4",
  fontWeight: "bold",
  cursor: "pointer",
  fontSize: 16,
};

export default P2PExchange;
