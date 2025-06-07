import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import MyTrades from "./MyTrades";
import TradePage from "./TradePage";
// ...

<Router>
  <Routes>
    <Route path="/trades/:adId" element={<TradePage />} />
    <Route path="/my-trades" element={<MyTrades />} />
    {/* другие маршруты */}
  </Routes>
</Router>
