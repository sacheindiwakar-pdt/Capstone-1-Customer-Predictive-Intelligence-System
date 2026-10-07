import {
  RefreshCw,
  Wifi,
  Server,
  Clock3,
} from "lucide-react";

function TopBar({ connected, loading, onRefresh, asOf }) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <div className="breadcrumb">
          <span>COMMAND CENTER</span>
          <b>/</b>
          <strong>NETWORK OVERVIEW</strong>
        </div>
      </div>

      <div className="topbar-right">
        <div className="topbar-status">
          <span
            className={`connection-dot ${
              connected ? "online" : "offline"
            }`}
          ></span>

          <Wifi size={15} />

          <span>
            {connected ? "API CONNECTED" : "API OFFLINE"}
          </span>
        </div>

        <div className="topbar-info">
          <Server size={15} />
          <span>FASTAPI</span>
        </div>

        {asOf && (
          <div className="topbar-info">
            <Clock3 size={15} />
            <span>{asOf}</span>
          </div>
        )}

        <button
          className="refresh-btn"
          onClick={onRefresh}
          disabled={loading}
        >
          <RefreshCw
            size={16}
            className={loading ? "spin" : ""}
          />
          Refresh
        </button>
      </div>
    </header>
  );
}

export default TopBar;