import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import Sidebar from "./components/Sidebar";

import Dashboard from "./pages/Dashboard";
import NetworkHealth from "./pages/NetworkHealth";
import Risk from "./pages/Risk";
import GridDetails from "./pages/GridDetails";
import HotspotsAlerts from "./pages/HotspotsAlerts";

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Sidebar />

        <div className="content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route
              path="/network-health"
              element={<NetworkHealth />}
            />
            <Route
              path="/alerts"
              element={<HotspotsAlerts />}
            />
            
            <Route
              path="/risk"
              element={<Risk />}
            />
            <Route
              path="/grid/:gridId"
              element={<GridDetails />}
            />
            <Route
              path="/grid"
              element={<GridDetails />}
            />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;