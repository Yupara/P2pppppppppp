import React from "react";
import { useNavigate } from "react-router-dom";

const ads = [
  { id: 1, name: "Savak", price: 70.96, amount: 304.7685, limits: "500 – 500 000 RUB" },
  { id: 2, name: "Ищу_Партнеров", price: 71.03, amount: 128.8821, limits: "500 – 500 000 RUB" },
];

function HomePage() {
  const navigate = useNavigate();

  return (
    <div>
      <h1>P2P Платформа Bybit</h1>
      {/* твой фильтр и меню здесь */}

      <div className="cards">
        {ads.map(ad => (
          <div key={ad.id} className="card">
            <div className="info">
              <div className="status online"></div>
              <img src="https://via.placeholder.com/50" alt="Avatar" />
              <div>
                <h3>{ad.name}</h3>
                <p>Цена: ₽{ad.price}</p>
                <p>Количество: {ad.amount} USDT</p>
                <p>Лимиты: {ad.limits}</p>
              </div>
            </div>
            <div className="actions">
              <button onClick={() => navigate(`/trade/${ad.id}`)}>Купить</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default HomePage;
