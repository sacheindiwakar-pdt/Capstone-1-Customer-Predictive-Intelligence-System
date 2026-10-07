import { useState } from "react";
import {
  Search,
  Activity,
  Phone,
  MessageSquare,
  Globe,
  BarChart3,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

import { getGridData } from "../services/networkApi";

function GridDetails() {
  const [gridInput, setGridInput] = useState("");
  const [gridId, setGridId] = useState("");
  const [gridData, setGridData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadGrid = async (id = gridInput) => {
    const cleanId = String(id).trim();

    if (!cleanId) {
      setError("Enter a grid ID to search.");
      setGridData(null);
      return;
    }

    setLoading(true);
    setError("");
    setGridData(null);

    try {
      const response = await getGridData(cleanId);

      if (
        !response ||
        !Array.isArray(response.activity_series) ||
        response.activity_series.length === 0
      ) {
        setGridId(cleanId);
        setError(`No activity data found for Grid ${cleanId}.`);
        return;
      }

      setGridId(response.grid_id ?? cleanId);
      setGridData(response);
    } catch (err) {
      console.error("Grid API error:", err);

      setGridId(cleanId);

      if (err.response?.status === 404) {
        setError(`Grid ${cleanId} was not found.`);
      } else if (err.response?.status === 500) {
        setError("The network API encountered an internal error.");
      } else if (err.code === "ERR_NETWORK") {
        setError(
          "Unable to connect to the network intelligence API."
        );
      } else {
        setError(
          err.response?.data?.detail ||
            `Unable to load Grid ${cleanId}.`
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    loadGrid();
  };

  const rows = gridData?.activity_series || [];

  const totals = rows.reduce(
    (acc, row) => {
      acc.calls += Number(row.total_calls || 0);
      acc.sms += Number(row.total_sms || 0);
      acc.internet += Number(row.internet_activity || 0);
      acc.total += Number(row.total_activity || 0);
      return acc;
    },
    {
      calls: 0,
      sms: 0,
      internet: 0,
      total: 0,
    }
  );

  const formatNumber = (value) =>
    Number(value || 0).toLocaleString(undefined, {
      maximumFractionDigits: 2,
    });

  const formatTime = (value) => {
    if (!value) return "-";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return String(value).replace("T", " ");
    }

    return date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  };

  const formatDateTime = (value) => {
    if (!value) return "-";

    return String(value)
      .replace("T", " ")
      .slice(0, 16);
  };

  return (
    <div className="grid-explorer-page">
      <div className="page-header">
        <div>
          <span className="section-label">
            GRID INTELLIGENCE
          </span>

          <h1>Grid Explorer</h1>

          <p>
            Analyze recent network activity for an
            individual telecom grid.
          </p>
        </div>

        {gridId && (
          <div className="selected-grid">
            <span>ACTIVE GRID</span>
            <strong>{gridId}</strong>
          </div>
        )}
      </div>

      <form
        className="grid-search-panel"
        onSubmit={handleSubmit}
      >
        <div className="search-icon">
          <Search size={22} />
        </div>

        <div className="search-field">
          <label htmlFor="grid-id">
            Grid ID
          </label>

          <input
            id="grid-id"
            type="text"
            placeholder="Enter grid ID e.g. 1"
            value={gridInput}
            onChange={(event) =>
              setGridInput(event.target.value)
            }
          />
        </div>

        <button
          type="submit"
          className="search-button"
          disabled={loading}
        >
          {loading ? (
            <>
              <RefreshCw
                size={18}
                className="spin"
              />
              Loading
            </>
          ) : (
            <>
              <Search size={18} />
              Explore Grid
            </>
          )}
        </button>
      </form>

      {error && (
        <div className="grid-error">
          <AlertTriangle size={20} />

          <div>
            <strong>Grid data unavailable</strong>
            <p>{error}</p>
          </div>
        </div>
      )}

      {loading && (
        <div className="grid-loading">
          <div className="loading-circle">
            <RefreshCw
              size={24}
              className="spin"
            />
          </div>

          <div>
            <strong>
              Querying network intelligence
            </strong>

            <p>
              Loading recent activity for Grid{" "}
              {gridInput}...
            </p>
          </div>
        </div>
      )}

      {gridData && !loading && (
        <>
          <div className="grid-kpi-grid">
            <div className="grid-kpi call">
              <div className="grid-kpi-icon">
                <Phone size={20} />
              </div>

              <div>
                <span>CALL ACTIVITY</span>
                <strong>
                  {formatNumber(totals.calls)}
                </strong>
              </div>
            </div>

            <div className="grid-kpi sms">
              <div className="grid-kpi-icon">
                <MessageSquare size={20} />
              </div>

              <div>
                <span>SMS ACTIVITY</span>
                <strong>
                  {formatNumber(totals.sms)}
                </strong>
              </div>
            </div>

            <div className="grid-kpi internet">
              <div className="grid-kpi-icon">
                <Globe size={20} />
              </div>

              <div>
                <span>INTERNET ACTIVITY</span>
                <strong>
                  {formatNumber(totals.internet)}
                </strong>
              </div>
            </div>

            <div className="grid-kpi total">
              <div className="grid-kpi-icon">
                <Activity size={20} />
              </div>

              <div>
                <span>TOTAL ACTIVITY</span>
                <strong>
                  {formatNumber(totals.total)}
                </strong>
              </div>
            </div>
          </div>

          <section className="grid-panel chart-panel">
            <div className="panel-heading">
              <div>
                <span>ACTIVITY TELEMETRY</span>
                <h2>
                  Grid {gridId} Activity Trend
                </h2>
              </div>

              <BarChart3 size={22} />
            </div>

            <div className="chart-container">
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <LineChart data={rows}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(255,255,255,0.08)"
                  />

                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={formatTime}
                    stroke="#64748b"
                    tick={{ fontSize: 11 }}
                  />

                  <YAxis
                    stroke="#64748b"
                    tick={{ fontSize: 11 }}
                  />

                  <Tooltip
                    contentStyle={{
                      background: "#101827",
                      border:
                        "1px solid rgba(255,255,255,0.1)",
                      borderRadius: "10px",
                      color: "#fff",
                    }}
                    labelFormatter={formatDateTime}
                  />

                  <Legend />

                  <Line
                    type="monotone"
                    dataKey="total_calls"
                    name="Calls"
                    stroke="#22d3ee"
                    strokeWidth={2}
                    dot={false}
                  />

                  <Line
                    type="monotone"
                    dataKey="total_sms"
                    name="SMS"
                    stroke="#a78bfa"
                    strokeWidth={2}
                    dot={false}
                  />

                  <Line
                    type="monotone"
                    dataKey="internet_activity"
                    name="Internet"
                    stroke="#34d399"
                    strokeWidth={2}
                    dot={false}
                  />

                  <Line
                    type="monotone"
                    dataKey="total_activity"
                    name="Total"
                    stroke="#f59e0b"
                    strokeWidth={3}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="grid-panel activity-table-panel">
            <div className="panel-heading">
              <div>
                <span>RAW ACTIVITY</span>
                <h2>Recent Grid Records</h2>
              </div>

              <div className="record-count">
                {gridData.hours_returned} hours
              </div>
            </div>

            <div className="activity-table-wrapper">
              <table className="activity-table">
                <thead>
                  <tr>
                    <th>TIME</th>
                    <th>CALL</th>
                    <th>SMS</th>
                    <th>INTERNET</th>
                    <th>TOTAL</th>
                  </tr>
                </thead>

                <tbody>
                  {rows.map((row, index) => (
                    <tr key={index}>
                      <td className="timestamp-cell">
                        {formatDateTime(
                          row.timestamp
                        )}
                      </td>

                      <td>
                        <span className="table-value call-value">
                          {formatNumber(
                            row.total_calls
                          )}
                        </span>
                      </td>

                      <td>
                        <span className="table-value sms-value">
                          {formatNumber(
                            row.total_sms
                          )}
                        </span>
                      </td>

                      <td>
                        <span className="table-value internet-value">
                          {formatNumber(
                            row.internet_activity
                          )}
                        </span>
                      </td>

                      <td>
                        <strong>
                          {formatNumber(
                            row.total_activity
                          )}
                        </strong>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <div className="grid-api-info">
            <span>
              REPORTING TIME
            </span>

            <strong>
              {formatDateTime(gridData.as_of)}
            </strong>
          </div>
        </>
      )}

      {!gridData &&
        !loading &&
        !error && (
          <div className="grid-empty">
            <div className="empty-icon">
              <Activity size={32} />
            </div>

            <span>GRID EXPLORER READY</span>

            <h2>
              Select a grid to begin
            </h2>

            <p>
              Enter a Grid ID above to retrieve recent
              call, SMS, internet and total network
              activity.
            </p>
          </div>
        )}
    </div>
  );
}

export default GridDetails;