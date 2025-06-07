function Dashboard() {
    const [ads, setAds] = React.useState([]);

    React.useEffect(() => {
        // Получаем объявления с сервера
        fetch("http://localhost:8000/api/ads")
            .then((response) => response.json())
            .then((data) => setAds(data))
            .catch((error) => console.error("Ошибка:", error));
    }, []);

    const handleBuy = (adId) => {
        fetch("http://localhost:8000/api/buy", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ adId }),
        })
            .then((response) => response.json())
            .then((data) => alert(data.message))
            .catch((error) => alert("Ошибка: " + error.message));
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
