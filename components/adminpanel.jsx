import React, { useState, useEffect } from "react";

function AdminPanel() {
    const [users, setUsers] = useState([]);
    const [trades, setTrades] = useState([]);
    const [disputes, setDisputes] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            const usersResponse = await fetch("/admin/users");
            const tradesResponse = await fetch("/trades/list");
            const disputesResponse = await fetch("/disputes/list");
            
            setUsers(await usersResponse.json());
            setTrades(await tradesResponse.json());
            setDisputes(await disputesResponse.json());
        };
        fetchData();
    }, []);

    return (
        <div>
            <h1>Admin Panel</h1>
            <h2>Users</h2>
            <ul>
                {users.map((user) => (
                    <li key={user.id}>{user.username} - {user.email}</li>
                ))}
            </ul>
            <h2>Trades</h2>
            <ul>
                {trades.map((trade) => (
                    <li key={trade.id}>{trade.amount} {trade.currency} - {trade.payment_method}</li>
                ))}
            </ul>
            <h2>Disputes</h2>
            <ul>
                {disputes.map((dispute) => (
                    <li key={dispute.id}>Trade ID: {dispute.trade_id}</li>
                ))}
            </ul>
        </div>
    );
}

export default AdminPanel;
