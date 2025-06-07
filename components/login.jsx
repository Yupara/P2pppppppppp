import React, { useState } from "react";

function Login() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState("");

    const handleLogin = async () => {
        try {
            const response = await fetch("http://localhost:8000/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email, password })
            });

            if (response.ok) {
                const data = await response.json();
                setMessage(data.message);
                console.log("Token:", data.token);
            } else {
                const errorData = await response.json();
                setMessage(errorData.detail);
            }
        } catch (error) {
            setMessage("Network error");
        }
    };

    return (
        <div style={{ maxWidth: 400, margin: "auto", padding: 20 }}>
            <h1>Login</h1>
            <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{ width: "100%", marginBottom: 10, padding: 8 }}
            />
            <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{ width: "100%", marginBottom: 10, padding: 8 }}
            />
            <button onClick={handleLogin} style={{ padding: 10, width: "100%" }}>
                Login
            </button>
            {message && <p style={{ marginTop: 10 }}>{message}</p>}
        </div>
    );
}

export default Login;
