import React from "react";
import { BrowserRouter as Router, Route, Switch } from "react-router-dom";

import Dashboard from "./components/dashboard";
import Login from "./components/login";
import AdminPanel from "./components/adminpanel";

function App() {
    return (
        <Router>
            <Switch>
                <Route path="/login" component={Login} />
                <Route path="/dashboard" component={Dashboard} />
                <Route path="/admin" component={AdminPanel} />
            </Switch>
        </Router>
    );
}

export default App;
