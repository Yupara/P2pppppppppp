import React, { useEffect, useState } from "react";
import AdList from "./AdList";
import Deal from "./Deal";

function App() {
    const [ads, setAds] = useState([]);
    const [type, setType] = useState("sell"); // Покупка или Продажа
    const [currentDeal, setCurrentDeal] = useState(null);

    useEffect(() => {
        fetch(`http://localhost:8000/ads?type=${type}`)
            .then(res => res.json())
            .then(data => setAds(data));
    }, [type]);

    if (currentDeal) {
        return <Deal deal={currentDeal} goBack={() => setCurrentDeal(null)} />
    }

    return (
        <div style={{ maxWidth: 800, margin: "auto", padding: 20, backgroundColor: "#002b26", color: "white", minHeight: "100vh" }}>
            <h1>P2P Платформа</h1>
            <div style={{ marginBottom: 20 }}>
                <button style={{ marginRight: 10, backgroundColor: type === "sell" ? "#90EE90" : "transparent" }} onClick={() => setType("sell")}>Продажа</button>
                <button style={{ backgroundColor: type === "buy" ? "#90EE90" : "transparent" }} onClick={() => setType("buy")}>Покупка</button>
            </div>

            <AdList ads={ads} onBuy={(ad) => setCurrentDeal({ ad, amount: "", user: "TestUser" })} />
        </div>
    );
}

export default App;
