import {
  CheckCircle2,
  Database,
  Globe2,
  Zap,
} from "lucide-react";

function NetworkStatus({ connected }) {
  return (
    <div className="panel network-status-panel">
      <div className="panel-header">
        <div>
          <div className="panel-kicker">SYSTEM STATUS</div>
          <h2>Platform Health</h2>
        </div>
      </div>

      <div className="health-list">
        <div className="health-row">
          <div className="health-icon">
            <Globe2 size={18} />
          </div>

          <div className="health-info">
            <strong>API Gateway</strong>
            <span>FastAPI service</span>
          </div>

          <div className={`health-state ${connected ? "ok" : "bad"}`}>
            <span></span>
            {connected ? "Online" : "Offline"}
          </div>
        </div>

        <div className="health-row">
          <div className="health-icon">
            <Database size={18} />
          </div>

          <div className="health-info">
            <strong>Network Data</strong>
            <span>Summary endpoint</span>
          </div>

          <div className={`health-state ${connected ? "ok" : "bad"}`}>
            <span></span>
            {connected ? "Available" : "Unavailable"}
          </div>
        </div>

        <div className="health-row">
          <div className="health-icon">
            <Zap size={18} />
          </div>

          <div className="health-info">
            <strong>Data Pipeline</strong>
            <span>Analytics layer</span>
          </div>

          <div className="health-state">
            <span></span>
            Ready
          </div>
        </div>
      </div>

      {connected && (
        <div className="healthy-message">
          <CheckCircle2 size={17} />
          <span>Network intelligence services are responding normally.</span>
        </div>
      )}
    </div>
  );
}

export default NetworkStatus;