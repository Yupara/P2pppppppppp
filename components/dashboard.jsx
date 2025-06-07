import React, { useState, useEffect } from "react";
import axios from "axios";

function Dashboard() {
    const [ads, setAds] = useState([]);

    useEffect(() => {
        axios.get("/api/ads").then((response) => {
            setAds(response.data);
        });
    }, []);

    const handleBuy = (adId) => {
        axios.post("/api/buy", { adId }).then((response) => {
            alert(response.data.message);
        });
    };

    return (
        <div>
            <h1>Объявления</h1>
            <ul>
                {ads.map((ad) => (
                    <li key={ad.id}>
                        {ad.currency} - {ad.amount} по {ad.price}
                        <button onClick={() => handleBuy(ad.id)}>Купить</button>
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default Dashboard;
