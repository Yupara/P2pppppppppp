import React from "react";
import ReactDOM from "react-dom";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";

function App() {
    return (
        <div>
            <Login />
            <Dashboard />
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById("root"));
