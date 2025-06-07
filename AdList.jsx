import React from "react";

export default function AdList({ ads, onBuy }) {
    return (
        <div>
            {ads.length === 0 && <p>Объявления не найдены</p>}
            {ads.map(ad => (
                <div key={ad.id} style={{ backgroundColor: "#003f35", padding: 15, borderRadius: 10, marginBottom: 10, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                        <b>{ad.user}</b> — {ad.coin} {ad.type === "sell" ? "продаёт" : "покупает"} по цене ₽{ad.price.toFixed(2)}
                        <p>Доступно: {ad.available}</p>
                        <p>Лимиты: {ad.limits}</p>
                        <p>Способы оплаты: {ad.payment_methods.join(", ")}</p>
                    </div>
                    <button style={{ padding: "10px 20px", backgroundColor: "#90EE90", color: "#003300", border: "none", borderRadius: 5, cursor: "pointer" }} onClick={() => onBuy(ad)}>
                        {ad.type === "sell" ? "Купить" : "Продать"}
                    </button>
                </div>
            ))}
        </div>
    )
}
