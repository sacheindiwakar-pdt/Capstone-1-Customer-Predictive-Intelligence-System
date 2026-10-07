import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  CheckCircle2,
  Database,
  Gauge,
  Radio,
  RefreshCw,
  Server,
  Wifi,
  Zap,
} from "lucide-react";

import {
  getNetworkSummary,
  getGridData,
} from "../services/networkApi";

function NetworkHealth() {
  const [summaryData, setSummaryData] = useState(null);
  const [gridData, setGridData] = useState(null);
  const [gridId, setGridId] = useState("100");
  const [loading, setLoading] = useState(true);
  const [gridLoading, setGridLoading] = useState(false);
  const [error, setError] = useState("");

  const loadSummary = async () => {
    try {
      setError("");
      const data = await getNetworkSummary();
      console.log("NETWORK SUMMARY:", data);
      setSummaryData(data);
    } catch (err) {
      console.error("NETWORK SUMMARY ERROR:", err);
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Failed to load network summary."
      );
    }
  };

  const loadGrid = async (id = gridId) => {
    try {
      setGridLoading(true);
      setError("");

      const data = await getGridData(Number(id));

      console.log(`GRID ${id} DATA:`, data);

      setGridData(data);
    } catch (err) {
      console.error(`GRID ${id} ERROR:`, err);

      setGridData(null);

      setError(
        err?.response?.data?.detail ||
          err?.message ||
          `Failed to load Grid ${id}.`
      );
    } finally {
      setGridLoading(false);
    }
  };

  const loadAll = async () => {
    setLoading(true);
    await Promise.all([
      loadSummary(),
      loadGrid(gridId),
    ]);
    setLoading(false);
  };

  useEffect(() => {
    loadAll();
  }, []);

  const networkActivity = useMemo(() => {
    const value =
      summaryData?.total_activity ??
      summaryData?.activity ??
      summaryData?.network_activity ??
      summaryData?.summary?.total_activity ??
      0;

    return Number(value);
  }, [summaryData]);

  const activeGrids = useMemo(() => {
    const value =
      summaryData?.active_grids ??
      summaryData?.activeGrids ??
      summaryData?.total_grids ??
      summaryData?.grid_count ??
      0;

    return Number(value);
  }, [summaryData]);

  const gridSummary = gridData?.summary || {};

  const activitySeries = Array.isArray(gridData?.activity_series)
    ? gridData.activity_series
    : [];

  const avgActivity = Number(
    gridSummary.avg_hourly_activity ?? 0
  );

  const peakActivity = Number(
    gridSummary.peak_activity ?? 0
  );

  const total24hActivity = Number(
    gridSummary.total_24h_activity ?? 0
  );

  const healthStatus = useMemo(() => {
    if (!gridData || activitySeries.length === 0) {
      return "NO DATA";
    }

    if (avgActivity <= 0) {
      return "NO DATA";
    }

    const peakRatio = peakActivity / avgActivity;

    if (peakRatio >= 3) {
      return "ATTENTION";
    }

    return "NORMAL";
  }, [gridData, activitySeries, avgActivity, peakActivity]);

  const chartMax = useMemo(() => {
    if (!activitySeries.length) return 1;

    return Math.max(
      ...activitySeries.map((item) =>
        Number(item.total_activity || 0)
      )
    );
  }, [activitySeries]);

  const activityStability = useMemo(() => {
    if (!activitySeries.length) return "NO DATA";

    const values = activitySeries.map((item) =>
      Number(item.total_activity || 0)
    );

    const average =
      values.reduce((sum, value) => sum + value, 0) /
      values.length;

    const variance =
      values.reduce(
        (sum, value) => sum + Math.pow(value - average, 2),
        0
      ) / values.length;

    const standardDeviation = Math.sqrt(variance);

    const coefficient =
      average > 0 ? standardDeviation / average : 0;

    if (coefficient < 0.5) return "STABLE";
    if (coefficient < 0.8) return "VARIABLE";

    return "HIGH VARIATION";
  }, [activitySeries]);

  const formatNumber = (value, decimals = 2) => {
    if (!Number.isFinite(Number(value))) return "0.00";

    return Number(value).toLocaleString("en-US", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  const formatCompact = (value) => {
    const number = Number(value);

    if (!Number.isFinite(number)) return "0";

    if (number >= 1_000_000_000) {
      return `${(number / 1_000_000_000).toFixed(2)}B`;
    }

    if (number >= 1_000_000) {
      return `${(number / 1_000_000).toFixed(2)}M`;
    }

    if (number >= 1_000) {
      return `${(number / 1_000).toFixed(2)}K`;
    }

    return number.toFixed(2);
  };

  const handleAnalyzeGrid = async (event) => {
    event.preventDefault();

    const id = Number(gridId);

    if (!Number.isInteger(id) || id <= 0) {
      setError("Please enter a valid grid ID.");
      return;
    }

    await loadGrid(id);
  };

  const getHealthClass = () => {
    if (healthStatus === "ATTENTION") return "attention";
    if (healthStatus === "NO DATA") return "nodata";
    return "normal";
  };

  return (
    <div className="network-health-page">
      <style>{`
        .network-health-page {
          color: #e8eef8;
          min-height: 100%;
          padding-bottom: 30px;
        }

        .nh-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          margin-bottom: 26px;
        }

        .nh-title-row {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .nh-title-icon {
          color: #7c83ff;
          width: 28px;
          height: 28px;
        }

        .nh-title {
          margin: 0;
          font-size: 28px;
          font-weight: 700;
          letter-spacing: -0.5px;
        }

        .nh-subtitle {
          margin: 6px 0 0 0;
          color: #8fa1bb;
          font-size: 14px;
        }

        .nh-refresh {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 9px 14px;
          border: 1px solid #27364d;
          background: #0d1420;
          color: #d9e4f5;
          border-radius: 9px;
          cursor: pointer;
          font-size: 13px;
        }

        .nh-refresh:hover {
          background: #131d2c;
        }

        .nh-refresh:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .nh-error {
          margin-bottom: 18px;
          padding: 12px 14px;
          border: 1px solid rgba(255, 80, 100, 0.35);
          background: rgba(255, 60, 80, 0.08);
          color: #ff9aa7;
          border-radius: 9px;
          font-size: 13px;
        }

        .nh-kpis {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 14px;
          margin-bottom: 22px;
        }

        .nh-card {
          background: #101823;
          border: 1px solid #243247;
          border-radius: 12px;
        }

        .nh-kpi {
          min-height: 96px;
          padding: 16px 18px;
        }

        .nh-kpi-label {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #6f85a3;
          font-size: 11px;
          letter-spacing: 0.7px;
          text-transform: uppercase;
        }

        .nh-kpi-label svg {
          width: 17px;
          height: 17px;
        }

        .nh-kpi-value {
          margin-top: 13px;
          font-size: 25px;
          font-weight: 700;
          color: #f3f7fc;
        }

        .nh-kpi-value.status {
          color: #20d36b;
        }

        .nh-monitor {
          padding: 18px;
          margin-bottom: 22px;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .nh-monitor-title {
          margin: 0;
          font-size: 16px;
        }

        .nh-monitor-subtitle {
          margin: 5px 0 0;
          color: #657b99;
          font-size: 12px;
        }

        .nh-grid-form {
          display: flex;
          gap: 9px;
        }

        .nh-grid-input {
          width: 108px;
          background: #090f19;
          border: 1px solid #2a3a51;
          color: #edf3fb;
          border-radius: 8px;
          padding: 9px 11px;
          outline: none;
        }

        .nh-grid-input:focus {
          border-color: #6570ff;
        }

        .nh-analyze {
          display: flex;
          align-items: center;
          gap: 7px;
          border: 0;
          background: #6366f1;
          color: white;
          border-radius: 8px;
          padding: 9px 14px;
          font-weight: 600;
          cursor: pointer;
        }

        .nh-analyze:hover {
          background: #7073ff;
        }

        .nh-main-grid {
          display: grid;
          grid-template-columns: 0.95fr 1.55fr;
          gap: 22px;
          margin-bottom: 22px;
        }

        .nh-grid-card {
          padding: 22px;
        }

        .nh-current-label {
          color: #7085a2;
          font-size: 11px;
          letter-spacing: 0.7px;
          text-transform: uppercase;
        }

        .nh-grid-heading {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 22px;
        }

        .nh-grid-id {
          margin-top: 5px;
          font-size: 24px;
          font-weight: 700;
        }

        .nh-connect-icon {
          width: 48px;
          height: 48px;
          display: grid;
          place-items: center;
          border-radius: 10px;
          background: rgba(18, 211, 107, 0.08);
          border: 1px solid rgba(18, 211, 107, 0.28);
          color: #20d36b;
        }

        .nh-health-box {
          text-align: center;
          padding: 20px;
          border-radius: 11px;
          border: 1px solid rgba(32, 211, 107, 0.25);
          background: rgba(32, 211, 107, 0.08);
          margin-bottom: 15px;
        }

        .nh-health-box.attention {
          border-color: rgba(255, 170, 50, 0.3);
          background: rgba(255, 170, 50, 0.08);
        }

        .nh-health-box.nodata {
          border-color: rgba(120, 140, 165, 0.25);
          background: rgba(120, 140, 165, 0.06);
        }

        .nh-health-icon {
          width: 28px;
          height: 28px;
          color: #20d36b;
        }

        .nh-health-box.attention .nh-health-icon {
          color: #ffb13b;
        }

        .nh-health-box.nodata .nh-health-icon {
          color: #8797ac;
        }

        .nh-health-text {
          margin-top: 8px;
          color: #20d36b;
          font-size: 22px;
          font-weight: 800;
        }

        .nh-health-box.attention .nh-health-text {
          color: #ffb13b;
        }

        .nh-health-box.nodata .nh-health-text {
          color: #8797ac;
        }

        .nh-health-caption {
          margin-top: 4px;
          color: #6f85a3;
          font-size: 11px;
        }

        .nh-stats {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 9px;
        }

        .nh-stat {
          padding: 11px 8px;
          text-align: center;
          background: #0a111c;
          border: 1px solid #243247;
          border-radius: 8px;
        }

        .nh-stat-label {
          color: #5e7491;
          font-size: 9px;
          text-transform: uppercase;
        }

        .nh-stat-value {
          margin-top: 5px;
          color: #e7eef9;
          font-size: 14px;
          font-weight: 700;
        }

        .nh-trend-card {
          padding: 22px;
          min-height: 340px;
        }

        .nh-section-heading {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 16px;
        }

        .nh-section-title {
          margin: 0;
          font-size: 16px;
        }

        .nh-section-subtitle {
          margin: 5px 0 0;
          color: #657b99;
          font-size: 11px;
        }

        .nh-trend-icon {
          color: #7c83ff;
        }

        .nh-chart {
          height: 240px;
          display: flex;
          align-items: flex-end;
          gap: 4px;
          padding: 15px 5px 5px;
          border-bottom: 1px solid #253349;
        }

        .nh-bar-wrap {
          flex: 1;
          height: 100%;
          display: flex;
          align-items: flex-end;
          min-width: 0;
        }

        .nh-bar {
          width: 100%;
          min-height: 3px;
          border-radius: 3px 3px 0 0;
          background: linear-gradient(
            to top,
            #4f46e5,
            #7c83ff
          );
          transition: height 0.3s ease;
          position: relative;
        }

        .nh-bar:hover {
          background: #9a9eff;
        }

        .nh-chart-labels {
          display: flex;
          justify-content: space-between;
          margin-top: 8px;
          color: #526782;
          font-size: 9px;
        }

        .nh-no-data {
          height: 260px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #506581;
          font-size: 12px;
        }

        .nh-indicators {
          padding: 20px;
        }

        .nh-indicator-title {
          display: flex;
          align-items: center;
          gap: 9px;
          margin-bottom: 15px;
        }

        .nh-indicator-title svg {
          color: #7c83ff;
        }

        .nh-indicator-title h3 {
          margin: 0;
          font-size: 16px;
        }

        .nh-indicator-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 12px;
        }

        .nh-indicator {
          padding: 15px;
          background: #0a111c;
          border: 1px solid #243247;
          border-radius: 9px;
        }

        .nh-indicator-label {
          display: flex;
          align-items: center;
          gap: 7px;
          color: #67809f;
          font-size: 11px;
        }

        .nh-indicator-label svg {
          width: 16px;
          height: 16px;
        }

        .nh-indicator-value {
          margin-top: 11px;
          font-size: 13px;
          font-weight: 700;
          color: #dce7f5;
        }

        .nh-footer-note {
          margin-top: 15px;
          color: #506581;
          font-size: 11px;
          display: flex;
          align-items: center;
          gap: 7px;
        }

        .nh-spinner {
          animation: nh-spin 1s linear infinite;
        }

        @keyframes nh-spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        @media (max-width: 1100px) {
          .nh-kpis {
            grid-template-columns: repeat(2, 1fr);
          }

          .nh-main-grid {
            grid-template-columns: 1fr;
          }

          .nh-indicator-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        @media (max-width: 700px) {
          .nh-header,
          .nh-monitor {
            flex-direction: column;
            gap: 15px;
          }

          .nh-kpis,
          .nh-indicator-grid {
            grid-template-columns: 1fr;
          }

          .nh-grid-form {
            width: 100%;
          }

          .nh-grid-input {
            flex: 1;
          }
        }
      `}</style>

      <div className="nh-header">
        <div>
          <div className="nh-title-row">
            <Activity className="nh-title-icon" />
            <h1 className="nh-title">Network Health</h1>
          </div>

          <p className="nh-subtitle">
            Monitor grid-level activity and overall network health.
          </p>
        </div>

        <button
          className="nh-refresh"
          onClick={loadAll}
          disabled={loading || gridLoading}
        >
          <RefreshCw
            size={15}
            className={
              loading || gridLoading ? "nh-spinner" : ""
            }
          />
          Refresh
        </button>
      </div>

      {error && (
        <div className="nh-error">
          {error}
        </div>
      )}

      <div className="nh-kpis">
        <KpiCard
          icon={<Activity />}
          label="Network Activity"
          value={
            loading
              ? "—"
              : formatCompact(networkActivity)
          }
        />

        <KpiCard
          icon={<Zap />}
          label="Peak Activity"
          value={
            gridData
              ? formatNumber(peakActivity)
              : "—"
          }
        />

        <KpiCard
          icon={<Server />}
          label="Active Grids"
          value={
            loading
              ? "—"
              : activeGrids
                ? formatNumber(activeGrids, 0)
                : "—"
          }
        />

        <KpiCard
          icon={<Gauge />}
          label="Health Status"
          value={
            gridData
              ? healthStatus
              : "—"
          }
          status
          statusClass={getHealthClass()}
        />
      </div>

      <div className="nh-card nh-monitor">
        <div>
          <h2 className="nh-monitor-title">
            Grid Health Monitor
          </h2>

          <p className="nh-monitor-subtitle">
            Select a grid to inspect its recent activity.
          </p>
        </div>

        <form
          className="nh-grid-form"
          onSubmit={handleAnalyzeGrid}
        >
          <input
            className="nh-grid-input"
            type="number"
            min="1"
            value={gridId}
            onChange={(e) => setGridId(e.target.value)}
            placeholder="Grid ID"
          />

          <button
            className="nh-analyze"
            type="submit"
            disabled={gridLoading}
          >
            {gridLoading ? (
              <RefreshCw
                size={15}
                className="nh-spinner"
              />
            ) : (
              <BarChart3 size={15} />
            )}
            Analyze Grid
          </button>
        </form>
      </div>

      <div className="nh-main-grid">
        <div className="nh-card nh-grid-card">
          <div className="nh-grid-heading">
            <div>
              <div className="nh-current-label">
                Current Grid
              </div>

              <div className="nh-grid-id">
                Grid #{gridData?.grid_id ?? gridId}
              </div>
            </div>

            <div className="nh-connect-icon">
              <Wifi size={24} />
            </div>
          </div>

          <div
            className={`nh-health-box ${getHealthClass()}`}
          >
            {healthStatus === "NORMAL" ? (
              <CheckCircle2 className="nh-health-icon" />
            ) : (
              <Gauge className="nh-health-icon" />
            )}

            <div className="nh-health-text">
              {healthStatus}
            </div>

            <div className="nh-health-caption">
              Network health indicator
            </div>
          </div>

          <div className="nh-stats">
            <MiniStat
              label="Average"
              value={formatNumber(avgActivity)}
            />

            <MiniStat
              label="Peak"
              value={formatNumber(peakActivity)}
            />

            <MiniStat
              label="24H Total"
              value={formatNumber(total24hActivity)}
            />
          </div>
        </div>

        <div className="nh-card nh-trend-card">
          <div className="nh-section-heading">
            <div>
              <h2 className="nh-section-title">
                Activity Trend
              </h2>

              <p className="nh-section-subtitle">
                Recent grid activity over the returned period.
              </p>
            </div>

            <Activity
              size={22}
              className="nh-trend-icon"
            />
          </div>

          {activitySeries.length > 0 ? (
            <>
              <div className="nh-chart">
                {activitySeries.map((item, index) => {
                  const value = Number(
                    item.total_activity || 0
                  );

                  const height =
                    chartMax > 0
                      ? Math.max(
                          (value / chartMax) * 100,
                          2
                        )
                      : 2;

                  return (
                    <div
                      className="nh-bar-wrap"
                      key={`${item.timestamp}-${index}`}
                      title={`${item.timestamp} — ${formatNumber(
                        value
                      )}`}
                    >
                      <div
                        className="nh-bar"
                        style={{
                          height: `${height}%`,
                        }}
                      />
                    </div>
                  );
                })}
              </div>

              <div className="nh-chart-labels">
                <span>
                  {activitySeries[0]?.timestamp
                    ? new Date(
                        activitySeries[0].timestamp
                      ).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : ""}
                </span>

                <span>
                  {activitySeries[
                    activitySeries.length - 1
                  ]?.timestamp
                    ? new Date(
                        activitySeries[
                          activitySeries.length - 1
                        ].timestamp
                      ).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : ""}
                </span>
              </div>
            </>
          ) : (
            <div className="nh-no-data">
              No activity series available for this grid.
            </div>
          )}
        </div>
      </div>

      <div className="nh-card nh-indicators">
        <div className="nh-indicator-title">
          <Gauge size={18} />
          <h3>Network Health Indicators</h3>
        </div>

        <div className="nh-indicator-grid">
          <HealthMetric
            icon={<Activity />}
            label="Activity Stability"
            value={activityStability}
          />

          <HealthMetric
            icon={<Wifi />}
            label="Grid Connectivity"
            value={gridData ? "AVAILABLE" : "UNAVAILABLE"}
          />

          <HealthMetric
            icon={<Database />}
            label="Data Coverage"
            value={`${activitySeries.length} POINTS`}
          />

          <HealthMetric
            icon={<Radio />}
            label="Monitoring State"
            value={
              gridData && activitySeries.length > 0
                ? "ACTIVE"
                : "NO DATA"
            }
          />
        </div>

        <div className="nh-footer-note">
          <Gauge size={13} />
          Health indicators are derived from the network
          activity data returned by the monitoring APIs.
        </div>
      </div>
    </div>
  );
}

function KpiCard({
  icon,
  label,
  value,
  status = false,
  statusClass = "",
}) {
  return (
    <div className="nh-card nh-kpi">
      <div className="nh-kpi-label">
        {icon}
        {label}
      </div>

      <div
        className={`nh-kpi-value ${
          status ? "status" : ""
        } ${statusClass}`}
      >
        {value}
      </div>
    </div>
  );
}

function MiniStat({ label, value }) {
  return (
    <div className="nh-stat">
      <div className="nh-stat-label">
        {label}
      </div>

      <div className="nh-stat-value">
        {value}
      </div>
    </div>
  );
}

function HealthMetric({ icon, label, value }) {
  return (
    <div className="nh-indicator">
      <div className="nh-indicator-label">
        {icon}
        {label}
      </div>

      <div className="nh-indicator-value">
        {value}
      </div>
    </div>
  );
}

export default NetworkHealth;