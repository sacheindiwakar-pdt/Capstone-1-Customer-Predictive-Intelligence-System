import { useEffect, useState } from "react";
import { AlertTriangle, Activity } from "lucide-react";

import { getNetworkSummary } from "../services/networkApi";

import StatusCard from "../components/StatusCard";
import ActivityPanel from "../components/ActivityPanel";
import NetworkStatus from "../components/NetworkStatus";
import TopBar from "../components/TopBar";

function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastFetchTime, setLastFetchTime] = useState(null);

  const loadSummary = async () => {
    try {
      setLoading(true);
      setError("");

      const start = performance.now();

      const data = await getNetworkSummary();

      const end = performance.now();

      setSummary(data);

      setLastFetchTime(Math.round(end - start));
    } catch (err) {
      console.error("Network summary error:", err);

      setError(
        err.response?.data?.detail ||
          "Unable to connect to the network intelligence API."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  const getValue = (...values) => {
    return values.find(
      (value) =>
        value !== undefined &&
        value !== null &&
        value !== ""
    ) ?? "—";
  };

  const totalActivity = getValue(
    summary?.total_activity,
    summary?.totalActivity,
    summary?.activity
  );

  const peakHour = getValue(
    summary?.peak_hour,
    summary?.peakHour,
    summary?.peak
  );

  const activeGrids = getValue(
    summary?.active_grids,
    summary?.activeGrids,
    summary?.grid_count
  );

  const highestGrid = getValue(
    summary?.highest_grid,
    summary?.highestGrid,
    summary?.top_grid
  );

  const asOf = summary?.as_of ?? summary?.asOf ?? "—";

  return (
    <div className="dashboard">
      <TopBar
        connected={!error && !!summary}
        loading={loading}
        onRefresh={loadSummary}
        asOf={!error && summary ? asOf : null}
      />

      <main className="dashboard-content">
        <section className="hero">
          <div>
            <div className="hero-label">
              <span></span>
              NETWORK INTELLIGENCE PLATFORM
            </div>

            <h1>
              Network
              <span> Overview</span>
            </h1>

            <p>
              Monitor network activity, identify peak periods,
              and track the highest-performing grids from a
              unified operational view.
            </p>
          </div>

          <div className="hero-status">
            <Activity size={19} />
            <div>
              <span>REPORTING DATA</span>
              <strong>{asOf}</strong>
            </div>
          </div>
        </section>

        {error && (
          <div className="error-banner">
            <div className="error-icon">
              <AlertTriangle size={20} />
            </div>

            <div>
              <strong>Network API unavailable</strong>
              <p>{error}</p>
            </div>

            <button onClick={loadSummary}>
              Retry
            </button>
          </div>
        )}

        {loading && !summary ? (
          <section className="loading-grid">
            {[1, 2, 3, 4].map((item) => (
              <div className="skeleton-card" key={item}>
                <div className="skeleton skeleton-small"></div>
                <div className="skeleton skeleton-large"></div>
                <div className="skeleton skeleton-medium"></div>
              </div>
            ))}
          </section>
        ) : (
          <>
            <section className="metrics-grid">
              <StatusCard
                title="TOTAL ACTIVITY"
                value={totalActivity}
                description="Aggregate network activity"
                type="activity"
                accent="blue"
              />

              <StatusCard
                title="PEAK HOUR"
                value={peakHour}
                description="Highest observed activity period"
                type="peak"
                accent="purple"
              />

              <StatusCard
                title="ACTIVE GRIDS"
                value={activeGrids}
                description="Network grids with activity"
                type="grids"
                accent="cyan"
              />

              <StatusCard
                title="HIGHEST GRID"
                value={highestGrid}
                description="Grid with highest activity"
                type="highest"
                accent="orange"
              />
            </section>

            <section className="main-panels">
              <ActivityPanel
                peakHour={peakHour}
                totalActivity={totalActivity}
              />

              <NetworkStatus connected={!error && !!summary} />
            </section>

            <section className="bottom-grid">
              <div className="report-card">
                <div className="report-header">
                  <div>
                    <span className="panel-kicker">
                      REPORTING WINDOW
                    </span>
                    <h3>Dataset Timestamp</h3>
                  </div>

                  <div className="timestamp-icon">
                    <Activity size={18} />
                  </div>
                </div>

                <div className="report-time">
                  {asOf}
                </div>

                <p>
                  This timestamp is provided by the network
                  intelligence API and represents the reporting
                  data time.
                </p>
              </div>

              <div className="performance-card">
                <div className="report-header">
                  <div>
                    <span className="panel-kicker">
                      API PERFORMANCE
                    </span>
                    <h3>Response Health</h3>
                  </div>

                  <div className="performance-value">
                    {lastFetchTime !== null
                      ? `${lastFetchTime} ms`
                      : "—"}
                  </div>
                </div>

                <div className="performance-track">
                  <div
                    className="performance-fill"
                    style={{
                      width: `${Math.min(
                        100,
                        Math.max(
                          20,
                          100 - (lastFetchTime || 0) / 10
                        )
                      )}%`,
                    }}
                  ></div>
                </div>

                <p>
                  Time taken to retrieve the network summary
                  from FastAPI.
                </p>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

export default Dashboard;