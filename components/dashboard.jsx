import React, { useEffect, useState } from "react";

function Dashboard() {
    const [trades, setTrades] = useState([]);

    useEffect(() => {
        const fetchTrades = async () => {
            const response = await fetch("/trades/list");
            const data = await response.json();
            setTrades(data);
        };
        fetchTrades();
    }, []);

    return (
        <div>
            <h1>Dashboard</h1>
            <h2>Open Trades</h2>
            <ul>
                {trades.map((trade) => (
                    <li key={trade.id}>
                        {trade.amount} {trade.currency} via {trade.payment_method}
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default Dashboard;
