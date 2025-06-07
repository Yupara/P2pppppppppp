import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import HomePage from "./HomePage";
import TradePage from "./TradePage";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/trade/:adId" element={<TradePage />} />
      </Routes>
    </Router>
  );
}

export default App;
