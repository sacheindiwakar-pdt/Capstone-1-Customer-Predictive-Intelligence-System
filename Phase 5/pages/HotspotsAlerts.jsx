import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  Flame,
  MapPin,
  RefreshCw,
  ShieldAlert,
  Activity,
  Filter,
  Clock,
  ChevronRight,
} from "lucide-react";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  CircleMarker,
  Tooltip,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import {
  getHotspots,
  getAlerts,
} from "../services/networkApi";

const MILAN_CENTER = [45.4642, 9.19];

const statusRank = {
  HIGH: 3,
  ATTENTION: 2,
  NORMAL: 1,
};

const statusColor = {
  HIGH: "#ef4444",
  ATTENTION: "#f59e0b",
  NORMAL: "#22c55e",
};

const statusBackground = {
  HIGH: "rgba(239,68,68,0.14)",
  ATTENTION: "rgba(245,158,11,0.14)",
  NORMAL: "rgba(34,197,94,0.14)",
};

const normalizeList = (response, key) => {
  if (Array.isArray(response)) return response;
  if (Array.isArray(response?.[key])) return response[key];
  if (Array.isArray(response?.data)) return response.data;
  if (Array.isArray(response?.results)) return response.results;
  return [];
};

const getGridId = (item) =>
  item?.grid_id ??
  item?.gridId ??
  item?.grid ??
  item?.cellId ??
  item?.cell_id ??
  item?.id;

const getGeoJsonGridId = (feature) =>
  feature?.properties?.cellId ??
  feature?.properties?.grid_id ??
  feature?.properties?.gridId ??
  feature?.properties?.cell_id ??
  feature?.properties?.id ??
  feature?.properties?.GRID_ID;

const normalizeStatus = (value) => {
  if (value === undefined || value === null) return null;

  const status = String(value).trim().toUpperCase();

  if (
    ["HIGH", "CRITICAL", "SEVERE", "CRITICAL_RISK"].includes(status)
  ) {
    return "HIGH";
  }

  if (
    ["ATTENTION", "MEDIUM", "WARNING", "MODERATE"].includes(status)
  ) {
    return "ATTENTION";
  }

  if (
    ["NORMAL", "LOW", "OK", "HEALTHY"].includes(status)
  ) {
    return "NORMAL";
  }

  return null;
};

const getStatus = (item) => {
  const directStatus =
    normalizeStatus(item?.risk_level) ||
    normalizeStatus(item?.severity) ||
    normalizeStatus(item?.status) ||
    normalizeStatus(item?.alert_status) ||
    normalizeStatus(item?.risk_status);

  if (directStatus) return directStatus;

  if (
    item?.high_activity_risk === true ||
    item?.high_activity_risk === 1
  ) {
    return "HIGH";
  }

  const riskScore = Number(item?.risk_score);

  if (!Number.isNaN(riskScore)) {
    const score = riskScore > 1 ? riskScore / 100 : riskScore;

    if (score >= 0.7) return "HIGH";
    if (score >= 0.4) return "ATTENTION";

    return "NORMAL";
  }

  const growth = Number(item?.activity_growth);

  if (!Number.isNaN(growth)) {
    if (growth >= 0.5) return "HIGH";
    if (growth >= 0.2) return "ATTENTION";
  }

  return "NORMAL";
};

const getActivity = (item) => {
  const values = [
    item?.activity,
    item?.total_activity,
    item?.avg_activity,
    item?.activity_value,
    item?.total_24h_activity,
  ];

  for (const value of values) {
    const number = Number(value);

    if (!Number.isNaN(number)) {
      return number;
    }
  }

  return 0;
};

const getTimestamp = (item) =>
  item?.timestamp ??
  item?.feature_timestamp ??
  item?.as_of ??
  item?.alert_timestamp ??
  item?.datetime ??
  item?.date_time;

const formatTime = (timestamp) => {
  if (!timestamp) return "--:--";

  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) {
    const match = String(timestamp).match(/\d{2}:\d{2}/);
    return match ? match[0] : "--:--";
  }

  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
};

const formatActivity = (value) =>
  Number(value || 0).toLocaleString(undefined, {
    maximumFractionDigits: 2,
  });

const getStatusStyle = (status) => ({
  display: "inline-flex",
  alignItems: "center",
  gap: "6px",
  padding: "5px 9px",
  borderRadius: "999px",
  fontSize: "11px",
  fontWeight: 700,
  letterSpacing: "0.4px",
  color: statusColor[status],
  background: statusBackground[status],
  border: `1px solid ${statusColor[status]}40`,
});

const getFeatureCenter = (feature) => {
  const geometry = feature?.geometry;

  if (!geometry) return null;

  let coordinates = [];

  if (geometry.type === "Polygon") {
    coordinates = geometry.coordinates?.[0] || [];
  }

  if (geometry.type === "MultiPolygon") {
    coordinates = geometry.coordinates?.[0]?.[0] || [];
  }

  if (!coordinates.length) return null;

  const latitudes = coordinates
    .map((point) => point?.[1])
    .filter((value) => typeof value === "number");

  const longitudes = coordinates
    .map((point) => point?.[0])
    .filter((value) => typeof value === "number");

  if (!latitudes.length || !longitudes.length) {
    return null;
  }

  const latitude =
    latitudes.reduce((sum, value) => sum + value, 0) /
    latitudes.length;

  const longitude =
    longitudes.reduce((sum, value) => sum + value, 0) /
    longitudes.length;

  return [latitude, longitude];
};

const HotspotsAlerts = () => {
  const navigate = useNavigate();

  const [hotspots, setHotspots] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [geojson, setGeojson] = useState(null);

  const [limit, setLimit] = useState(10);
  const [severity, setSeverity] = useState("ALL");

  const [loading, setLoading] = useState(true);
  const [mapLoading, setMapLoading] = useState(true);

  const [error, setError] = useState("");
  const [selectedGrid, setSelectedGrid] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError("");

        const [hotspotResponse, alertResponse] = await Promise.all([
          getHotspots(limit),
          getAlerts(limit, severity),
        ]);

        const hotspotList = normalizeList(
          hotspotResponse,
          "hotspots"
        );

        const alertList = normalizeList(
          alertResponse,
          "alerts"
        );

        setHotspots(hotspotList);
        setAlerts(alertList);

        console.log("HOTSPOTS API:", hotspotResponse);
        console.log("ALERTS API:", alertResponse);
      } catch (err) {
        console.error("Network data error:", err);

        setError(
          err?.response?.data?.detail ||
            err?.message ||
            "Unable to load hotspot and alert data."
        );

        setHotspots([]);
        setAlerts([]);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [limit, severity]);

  useEffect(() => {
    const loadGeoJson = async () => {
      try {
        setMapLoading(true);

        const response = await fetch(
          "/reference/milano-grid.geojson"
        );

        if (!response.ok) {
          throw new Error(
            `GeoJSON request failed: ${response.status}`
          );
        }

        const data = await response.json();

        console.log("MILAN GEOJSON:", data);

        setGeojson(data);
      } catch (err) {
        console.error("GeoJSON error:", err);
      } finally {
        setMapLoading(false);
      }
    };

    loadGeoJson();
  }, []);

  const rankedHotspots = useMemo(() => {
    return hotspots
      .map((item) => ({
        ...item,
        gridId: getGridId(item),
        status: getStatus(item),
        activity: getActivity(item),
        timestamp: getTimestamp(item),
      }))
      .filter(
        (item) =>
          item.gridId !== undefined &&
          item.gridId !== null
      )
      .filter(
        (item) =>
          severity === "ALL" ||
          item.status === severity
      )
      .sort((a, b) => {
        const statusDifference =
          statusRank[b.status] - statusRank[a.status];

        if (statusDifference !== 0) {
          return statusDifference;
        }

        return b.activity - a.activity;
      })
      .slice(0, limit);
  }, [hotspots, severity, limit]);

  const filteredAlerts = useMemo(() => {
    return alerts
      .map((item) => ({
        ...item,
        gridId: getGridId(item),
        status: getStatus(item),
        activity: getActivity(item),
        timestamp: getTimestamp(item),
      }))
      .filter(
        (item) =>
          item.gridId !== undefined &&
          item.gridId !== null
      )
      .filter(
        (item) =>
          severity === "ALL" ||
          item.status === severity
      )
      .sort(
        (a, b) =>
          statusRank[b.status] - statusRank[a.status]
      )
      .slice(0, limit);
  }, [alerts, severity, limit]);

  const gridStatus = useMemo(() => {
    const statusMap = {};

    const addStatus = (item) => {
      const gridId = getGridId(item);

      if (
        gridId === undefined ||
        gridId === null
      ) {
        return;
      }

      const status = getStatus(item);
      const key = String(gridId);

      if (
        !statusMap[key] ||
        statusRank[status] >
          statusRank[statusMap[key]]
      ) {
        statusMap[key] = status;
      }
    };

    hotspots.forEach(addStatus);
    alerts.forEach(addStatus);

    return statusMap;
  }, [hotspots, alerts]);

  const getPolygonStyle = (feature) => {
    const gridId = getGeoJsonGridId(feature);

    const status =
      gridStatus[String(gridId)] || "NORMAL";

    const isSelected =
      selectedGrid !== null &&
      String(selectedGrid) === String(gridId);

    return {
      color: isSelected
        ? "#ffffff"
        : statusColor[status],

      weight: isSelected ? 3 : 1.5,

      fillColor: statusColor[status],

      fillOpacity: isSelected ? 0.55 : 0.25,
    };
  };

  const onEachFeature = (feature, layer) => {
    const gridId = getGeoJsonGridId(feature);

    const status =
      gridStatus[String(gridId)] || "NORMAL";

    layer.bindTooltip(
      `<div style="font-family:Inter,sans-serif">
        <strong>Grid ${gridId}</strong><br/>
        Status: <strong>${status}</strong>
      </div>`,
      {
        sticky: true,
      }
    );

    layer.on({
      click: () => setSelectedGrid(gridId),

      mouseover: (event) => {
        event.target.setStyle({
          weight: 3,
          fillOpacity: 0.5,
        });
      },

      mouseout: (event) => {
        event.target.setStyle(
          getPolygonStyle(feature)
        );
      },
    });
  };

  const mapPoints = useMemo(() => {
    if (!geojson?.features) {
      return [];
    }

    return geojson.features
      .map((feature) => {
        const gridId =
          getGeoJsonGridId(feature);

        if (
          gridId === undefined ||
          gridId === null
        ) {
          return null;
        }

        const position =
          getFeatureCenter(feature);

        if (!position) {
          return null;
        }

        const status =
          gridStatus[String(gridId)] ||
          "NORMAL";

        return {
          gridId,
          status,
          position,
        };
      })
      .filter(Boolean);
  }, [geojson, gridStatus]);

  useEffect(() => {
    console.log("GRID STATUS:", gridStatus);
    console.log("MAP POINTS:", mapPoints);
    console.log(
      "GEOJSON FEATURES:",
      geojson?.features?.length
    );
  }, [gridStatus, mapPoints, geojson]);

  const highCount = useMemo(
    () =>
      Object.values(gridStatus).filter(
        (status) => status === "HIGH"
      ).length,
    [gridStatus]
  );

  const attentionCount = useMemo(
    () =>
      Object.values(gridStatus).filter(
        (status) => status === "ATTENTION"
      ).length,
    [gridStatus]
  );

  const normalCount = useMemo(
    () =>
      Object.values(gridStatus).filter(
        (status) => status === "NORMAL"
      ).length,
    [gridStatus]
  );

  const refreshData = () => {
    window.location.reload();
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#090d16",
        color: "#f8fafc",
        padding: "28px",
        fontFamily: "Inter, sans-serif",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "24px",
        }}
      >
        <div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
            }}
          >
            <Flame size={25} color="#f97316" />

            <h1
              style={{
                margin: 0,
                fontSize: "25px",
                fontWeight: 750,
              }}
            >
              Hotspots & Alerts
            </h1>
          </div>

          <p
            style={{
              margin: "7px 0 0",
              color: "#94a3b8",
              fontSize: "13px",
            }}
          >
            Network activity hotspots, risk levels and
            operational alerts across Milan.
          </p>
        </div>

        <button
          onClick={refreshData}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "10px 14px",
            borderRadius: "8px",
            border: "1px solid #273449",
            background: "#111827",
            color: "#e2e8f0",
            cursor: "pointer",
          }}
        >
          <RefreshCw size={15} />
          Refresh
        </button>
      </div>

      {error && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            padding: "12px 15px",
            marginBottom: "18px",
            borderRadius: "9px",
            background: "rgba(239,68,68,0.1)",
            border:
              "1px solid rgba(239,68,68,0.35)",
            color: "#fca5a5",
            fontSize: "13px",
          }}
        >
          <AlertTriangle size={17} />
          {error}
        </div>
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(4,minmax(0,1fr))",
          gap: "14px",
          marginBottom: "20px",
        }}
      >
        {[
          {
            label: "High Risk",
            value: highCount,
            icon: ShieldAlert,
            color: "#ef4444",
          },
          {
            label: "Attention",
            value: attentionCount,
            icon: AlertTriangle,
            color: "#f59e0b",
          },
          {
            label: "Normal",
            value: normalCount,
            icon: Activity,
            color: "#22c55e",
          },
          {
            label: "Tracked Grids",
            value: Object.keys(gridStatus).length,
            icon: MapPin,
            color: "#60a5fa",
          },
        ].map((item) => {
          const Icon = item.icon;

          return (
            <div
              key={item.label}
              style={{
                background: "#101722",
                border: "1px solid #1f2b3d",
                borderRadius: "12px",
                padding: "17px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent:
                    "space-between",
                  alignItems: "center",
                }}
              >
                <span
                  style={{
                    color: "#94a3b8",
                    fontSize: "12px",
                  }}
                >
                  {item.label}
                </span>

                <Icon
                  size={17}
                  color={item.color}
                />
              </div>

              <div
                style={{
                  marginTop: "10px",
                  fontSize: "25px",
                  fontWeight: 750,
                }}
              >
                {item.value}
              </div>
            </div>
          );
        })}
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "15px",
          padding: "13px 15px",
          marginBottom: "20px",
          background: "#101722",
          border: "1px solid #1f2b3d",
          borderRadius: "10px",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "9px",
            color: "#94a3b8",
            fontSize: "12px",
          }}
        >
          <Filter size={15} />
          Filters
        </div>

        <div
          style={{
            display: "flex",
            gap: "10px",
          }}
        >
          <select
            value={severity}
            onChange={(event) =>
              setSeverity(event.target.value)
            }
            style={{
              background: "#0b111b",
              color: "#e2e8f0",
              border: "1px solid #29364a",
              borderRadius: "7px",
              padding: "8px 11px",
              outline: "none",
            }}
          >
            <option value="ALL">
              All Severity
            </option>

            <option value="HIGH">
              High
            </option>

            <option value="ATTENTION">
              Attention
            </option>

            <option value="NORMAL">
              Normal
            </option>
          </select>

          <select
            value={limit}
            onChange={(event) =>
              setLimit(Number(event.target.value))
            }
            style={{
              background: "#0b111b",
              color: "#e2e8f0",
              border: "1px solid #29364a",
              borderRadius: "7px",
              padding: "8px 11px",
              outline: "none",
            }}
          >
            <option value={5}>Top 5</option>
            <option value={10}>Top 10</option>
            <option value={20}>Top 20</option>
            <option value={50}>Top 50</option>
          </select>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "minmax(0,1fr) minmax(0,1fr)",
          gap: "20px",
        }}
      >
        <div
          style={{
            background: "#101722",
            border: "1px solid #1f2b3d",
            borderRadius: "12px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "17px",
              borderBottom:
                "1px solid #1f2b3d",
              display: "flex",
              justifyContent:
                "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <h2
                style={{
                  margin: 0,
                  fontSize: "15px",
                }}
              >
                Network Hotspots
              </h2>

              <p
                style={{
                  margin: "5px 0 0",
                  color: "#64748b",
                  fontSize: "11px",
                }}
              >
                Highest activity grids
              </p>
            </div>

            <Flame
              size={17}
              color="#f97316"
            />
          </div>

          <div
            style={{
              overflowX: "auto",
            }}
          >
            <table
              style={{
                width: "100%",
                borderCollapse:
                  "collapse",
              }}
            >
              <thead>
                <tr>
                  {[
                    "Grid",
                    "Activity",
                    "Status",
                    "Time",
                    "",
                  ].map((heading) => (
                    <th
                      key={heading}
                      style={{
                        textAlign: "left",
                        padding:
                          "11px 15px",
                        color: "#64748b",
                        fontSize: "10px",
                        textTransform:
                          "uppercase",
                        letterSpacing:
                          "0.5px",
                        borderBottom:
                          "1px solid #1f2b3d",
                      }}
                    >
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {loading ? (
                  <tr>
                    <td
                      colSpan={5}
                      style={{
                        padding: "30px",
                        textAlign:
                          "center",
                        color:
                          "#64748b",
                      }}
                    >
                      Loading hotspots...
                    </td>
                  </tr>
                ) : rankedHotspots.length === 0 ? (
                  <tr>
                    <td
                      colSpan={5}
                      style={{
                        padding: "30px",
                        textAlign:
                          "center",
                        color:
                          "#64748b",
                      }}
                    >
                      No hotspot data
                      available.
                    </td>
                  </tr>
                ) : (
                  rankedHotspots.map(
                    (item) => (
                      <tr
                        key={`hotspot-${item.gridId}`}
                        onClick={() =>
                          setSelectedGrid(
                            item.gridId
                          )
                        }
                        style={{
                          cursor:
                            "pointer",
                          borderBottom:
                            "1px solid #172131",
                        }}
                      >
                        <td
                          style={{
                            padding:
                              "12px 15px",
                            fontFamily:
                              "JetBrains Mono, monospace",
                            fontSize:
                              "12px",
                          }}
                        >
                          #{item.gridId}
                        </td>

                        <td
                          style={{
                            padding:
                              "12px 15px",
                            fontSize:
                              "12px",
                          }}
                        >
                          {formatActivity(
                            item.activity
                          )}
                        </td>

                        <td
                          style={{
                            padding:
                              "12px 15px",
                          }}
                        >
                          <span
                            style={getStatusStyle(
                              item.status
                            )}
                          >
                            {item.status}
                          </span>
                        </td>

                        <td
                          style={{
                            padding:
                              "12px 15px",
                            color:
                              "#94a3b8",
                            fontSize:
                              "11px",
                          }}
                        >
                          {formatTime(
                            item.timestamp
                          )}
                        </td>

                        <td>
                          <ChevronRight
                            size={15}
                            color="#64748b"
                          />
                        </td>
                      </tr>
                    )
                  )
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div
          style={{
            background: "#101722",
            border: "1px solid #1f2b3d",
            borderRadius: "12px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "17px",
              borderBottom:
                "1px solid #1f2b3d",
              display: "flex",
              justifyContent:
                "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <h2
                style={{
                  margin: 0,
                  fontSize: "15px",
                }}
              >
                Network Alerts
              </h2>

              <p
                style={{
                  margin: "5px 0 0",
                  color: "#64748b",
                  fontSize: "11px",
                }}
              >
                Risk and operational events
              </p>
            </div>

            <ShieldAlert
              size={17}
              color="#ef4444"
            />
          </div>

          <div
            style={{
              overflowX: "auto",
            }}
          >
            <table
              style={{
                width: "100%",
                borderCollapse:
                  "collapse",
              }}
            >
              <thead>
                <tr>
                  {[
                    "Grid",
                    "Status",
                    "Activity",
                    "Time",
                    "",
                  ].map((heading) => (
                    <th
                      key={heading}
                      style={{
                        textAlign: "left",
                        padding:
                          "11px 15px",
                        color: "#64748b",
                        fontSize: "10px",
                        textTransform:
                          "uppercase",
                        letterSpacing:
                          "0.5px",
                        borderBottom:
                          "1px solid #1f2b3d",
                      }}
                    >
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {loading ? (
                  <tr>
                    <td
                      colSpan={5}
                      style={{
                        padding: "30px",
                        textAlign:
                          "center",
                        color:
                          "#64748b",
                      }}
                    >
                      Loading alerts...
                    </td>
                  </tr>
                ) : filteredAlerts.length === 0 ? (
                  <tr>
                    <td
                      colSpan={5}
                      style={{
                        padding: "30px",
                        textAlign:
                          "center",
                        color:
                          "#64748b",
                      }}
                    >
                      No alert data
                      available.
                    </td>
                  </tr>
                ) : (
                  filteredAlerts.map(
                    (item, index) => (
                      <tr
                        key={`alert-${item.gridId}-${index}`}
                        onClick={() =>
                          navigate(
                            `/grid/${item.gridId}`
                          )
                        }
                        style={{
                          cursor:
                            "pointer",
                          borderBottom:
                            "1px solid #172131",
                        }}
                      >
                        <td
                          style={{
                            padding:
                              "12px 15px",
                            fontFamily:
                              "JetBrains Mono, monospace",
                            fontSize:
                              "12px",
                          }}
                        >
                          #{item.gridId}
                        </td>

                        <td
                          style={{
                            padding:
                              "12px 15px",
                          }}
                        >
                          <span
                            style={getStatusStyle(
                              item.status
                            )}
                          >
                            {item.status}
                          </span>
                        </td>

                        <td
                          style={{
                            padding:
                              "12px 15px",
                            fontSize:
                              "12px",
                          }}
                        >
                          {formatActivity(
                            item.activity
                          )}
                        </td>

                        <td
                          style={{
                            padding:
                              "12px 15px",
                            color:
                              "#94a3b8",
                            fontSize:
                              "11px",
                          }}
                        >
                          {formatTime(
                            item.timestamp
                          )}
                        </td>

                        <td>
                          <ChevronRight
                            size={15}
                            color="#64748b"
                          />
                        </td>
                      </tr>
                    )
                  )
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div
        style={{
          marginTop: "20px",
          background: "#101722",
          border: "1px solid #1f2b3d",
          borderRadius: "12px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: "17px",
            display: "flex",
            justifyContent:
              "space-between",
            alignItems: "center",
            borderBottom:
              "1px solid #1f2b3d",
          }}
        >
          <div>
            <h2
              style={{
                margin: 0,
                fontSize: "15px",
                display: "flex",
                alignItems:
                  "center",
                gap: "8px",
              }}
            >
              <MapPin
                size={17}
                color="#60a5fa"
              />
              Milan Network Grid
            </h2>

            <p
              style={{
                margin: "5px 0 0",
                color: "#64748b",
                fontSize: "11px",
              }}
            >
              Geographic intelligence for
              network activity and risk.
            </p>
          </div>

          <div
            style={{
              display: "flex",
              gap: "14px",
              alignItems: "center",
            }}
          >
            {[
              "NORMAL",
              "ATTENTION",
              "HIGH",
            ].map((status) => (
              <div
                key={status}
                style={{
                  display: "flex",
                  alignItems:
                    "center",
                  gap: "6px",
                  color: "#94a3b8",
                  fontSize: "11px",
                }}
              >
                <span
                  style={{
                    width: "9px",
                    height: "9px",
                    borderRadius:
                      "50%",
                    background:
                      statusColor[
                        status
                      ],
                    boxShadow: `0 0 7px ${statusColor[status]}`,
                  }}
                />

                {status}
              </div>
            ))}
          </div>
        </div>

        <div
          style={{
            height: "520px",
            position: "relative",
          }}
        >
          {mapLoading && (
            <div
              style={{
                position:
                  "absolute",
                zIndex: 1000,
                top: "15px",
                left: "15px",
                padding:
                  "8px 11px",
                borderRadius: "7px",
                background:
                  "rgba(9,13,22,0.9)",
                border:
                  "1px solid #29364a",
                color: "#94a3b8",
                fontSize: "11px",
              }}
            >
              Loading Milan grid...
            </div>
          )}

          <MapContainer
            center={MILAN_CENTER}
            zoom={11}
            minZoom={9}
            maxZoom={16}
            scrollWheelZoom={true}
            style={{
              height: "100%",
              width: "100%",
              background: "#dbe4ea",
            }}
            whenReady={(event) => {
              setTimeout(() => {
                event.target.invalidateSize();
              }, 150);
            }}
          >
            <TileLayer
              attribution="&copy; OpenStreetMap contributors"
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              maxZoom={19}
            />

            {geojson && (
              <GeoJSON
                data={geojson}
                style={getPolygonStyle}
                onEachFeature={
                  onEachFeature
                }
              />
            )}

            {mapPoints.map((point) => (
              <CircleMarker
                key={`point-${point.gridId}`}
                center={point.position}
                radius={
                  point.status ===
                  "HIGH"
                    ? 8
                    : point.status ===
                        "ATTENTION"
                      ? 7
                      : 5
                }
                pathOptions={{
                  color: "#ffffff",
                  weight: 2,
                  fillColor:
                    statusColor[
                      point.status
                    ],
                  fillOpacity: 1,
                }}
                eventHandlers={{
                  click: () =>
                    setSelectedGrid(
                      point.gridId
                    ),
                }}
              >
                <Tooltip>
                  <div
                    style={{
                      minWidth: "100px",
                    }}
                  >
                    <strong>
                      Grid{" "}
                      {point.gridId}
                    </strong>

                    <br />

                    Status:{" "}
                    <strong
                      style={{
                        color:
                          statusColor[
                            point.status
                          ],
                      }}
                    >
                      {point.status}
                    </strong>
                  </div>
                </Tooltip>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>
      </div>

      {selectedGrid !== null && (
        <div
          style={{
            marginTop: "16px",
            padding: "14px 17px",
            background: "#111827",
            border: "1px solid #303b52",
            borderRadius: "10px",
            display: "flex",
            alignItems: "center",
            justifyContent:
              "space-between",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems:
                "center",
              gap: "10px",
            }}
          >
            <MapPin
              size={17}
              color="#818cf8"
            />

            <div>
              <div
                style={{
                  fontSize: "12px",
                  color: "#64748b",
                }}
              >
                Selected Grid
              </div>

              <div
                style={{
                  marginTop: "2px",
                  fontSize: "14px",
                  fontWeight: 700,
                }}
              >
                Grid #{selectedGrid}
              </div>
            </div>
          </div>

          <button
            onClick={() =>
              navigate(
                `/grid/${selectedGrid}`
              )
            }
            style={{
              display: "flex",
              alignItems:
                "center",
              gap: "7px",
              padding:
                "9px 13px",
              border: "none",
              borderRadius: "7px",
              background: "#6366f1",
              color: "#ffffff",
              fontSize: "12px",
              fontWeight: 650,
              cursor: "pointer",
            }}
          >
            Open Grid Explorer
            <ChevronRight size={14} />
          </button>
        </div>
      )}

      <div
        style={{
          display: "flex",
          alignItems:
            "center",
          gap: "7px",
          marginTop: "15px",
          color: "#475569",
          fontSize: "10px",
        }}
      >
        <Clock size={12} />
        Milan grid boundaries are loaded once
        from the static GeoJSON reference.
      </div>
    </div>
  );
};

export default HotspotsAlerts;