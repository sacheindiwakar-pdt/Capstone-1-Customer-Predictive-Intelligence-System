import { useState } from "react";
import {
  Activity,
  AlertTriangle,
  Brain,
  CheckCircle2,
  Clock,
  Gauge,
  Info,
  Loader2,
  ShieldAlert,
  Sparkles,
  Target,
} from "lucide-react";
import { predictNetworkRisk } from "../services/networkApi";

const normalizeRiskLevel = (value) => {
  if (value === undefined || value === null) return "UNKNOWN";

  const level = String(value).trim().toUpperCase();

  if (["HIGH", "CRITICAL", "SEVERE", "CRITICAL_RISK"].includes(level)) {
    return "HIGH";
  }

  if (["ATTENTION", "MEDIUM", "MODERATE", "WARNING"].includes(level)) {
    return "ATTENTION";
  }

  if (["NORMAL", "LOW", "HEALTHY", "OK"].includes(level)) {
    return "NORMAL";
  }

  return level;
};

const getRiskColor = (level) => {
  if (level === "HIGH") return "#ef4444";
  if (level === "ATTENTION") return "#f59e0b";
  if (level === "NORMAL") return "#22c55e";
  return "#94a3b8";
};

const getRiskBackground = (level) => {
  if (level === "HIGH") return "rgba(239,68,68,0.12)";
  if (level === "ATTENTION") return "rgba(245,158,11,0.12)";
  if (level === "NORMAL") return "rgba(34,197,94,0.12)";
  return "rgba(148,163,184,0.10)";
};

const getRiskScore = (response) => {
  const values = [
    response?.risk_score,
    response?.score,
    response?.riskScore,
    response?.prediction?.risk_score,
    response?.prediction?.score,
    response?.result?.risk_score,
    response?.result?.score,
  ];

  for (const value of values) {
    const number = Number(value);

    if (!Number.isNaN(number)) {
      return number;
    }
  }

  return null;
};

const getRiskLevel = (response, score) => {
  const values = [
    response?.risk_level,
    response?.riskLevel,
    response?.level,
    response?.prediction?.risk_level,
    response?.prediction?.riskLevel,
    response?.result?.risk_level,
    response?.result?.riskLevel,
  ];

  for (const value of values) {
    if (value !== undefined && value !== null) {
      return normalizeRiskLevel(value);
    }
  }

  if (score !== null) {
    const normalizedScore = score > 1 ? score / 100 : score;

    if (normalizedScore >= 0.7) return "HIGH";
    if (normalizedScore >= 0.4) return "ATTENTION";

    return "NORMAL";
  }

  return "UNKNOWN";
};

const getModelVersion = (response) => {
  return (
    response?.model_version ??
    response?.modelVersion ??
    response?.version ??
    response?.prediction?.model_version ??
    response?.prediction?.modelVersion ??
    response?.result?.model_version ??
    response?.result?.modelVersion ??
    "N/A"
  );
};

const getGridId = (response) => {
  return (
    response?.grid_id ??
    response?.gridId ??
    response?.prediction?.grid_id ??
    response?.prediction?.gridId ??
    response?.result?.grid_id ??
    response?.result?.gridId ??
    null
  );
};

const formatScore = (score) => {
  if (score === null || score === undefined) return "—";

  const number = Number(score);

  if (Number.isNaN(number)) return "—";

  return number <= 1
    ? `${(number * 100).toFixed(1)}%`
    : `${number.toFixed(1)}%`;
};

const Risk = () => {
  const [form, setForm] = useState({
    grid_id: "",
    avg_activity: "",
    activity_growth: "",
    active_hours: "",
    peak_ratio: "",
    variability: "",
    internet_share: "",
    activity_vs_baseline: "",
    baseline_gap: "",
    feature_timestamp: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [prediction, setPrediction] = useState(null);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handlePredict = async (event) => {
    event.preventDefault();

    setError("");
    setPrediction(null);

    if (!form.grid_id.trim()) {
      setError("Please enter a Grid ID.");
      return;
    }

    const requiredFields = [
      "avg_activity",
      "activity_growth",
      "active_hours",
      "peak_ratio",
      "variability",
      "internet_share",
      "activity_vs_baseline",
      "baseline_gap",
      "feature_timestamp",
    ];

    const missingField = requiredFields.find(
      (field) => form[field] === ""
    );

    if (missingField) {
      setError(
        `Please enter a value for ${missingField.replaceAll("_", " ")}.`
      );
      return;
    }

    const payload = {
      grid_id: Number(form.grid_id),
      avg_activity: Number(form.avg_activity),
      activity_growth: Number(form.activity_growth),
      active_hours: Number(form.active_hours),
      peak_ratio: Number(form.peak_ratio),
      variability: Number(form.variability),
      internet_share: Number(form.internet_share),
      activity_vs_baseline: Number(form.activity_vs_baseline),
      baseline_gap: Number(form.baseline_gap),
      feature_timestamp: form.feature_timestamp,
    };

    try {
      setLoading(true);

      console.log("PREDICTION REQUEST:", payload);

      const response = await predictNetworkRisk(payload);

      console.log("PREDICTION RESPONSE:", response);

      const score = getRiskScore(response);
      const level = getRiskLevel(response, score);
      const version = getModelVersion(response);
      const responseGridId = getGridId(response);

      setPrediction({
        raw: response,
        score,
        level,
        version,
        gridId: responseGridId ?? form.grid_id,
      });
    } catch (err) {
      console.error("Prediction error:", err);

      const detail =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.message ||
        "Unable to generate a risk prediction.";

      setError(
        typeof detail === "string"
          ? detail
          : JSON.stringify(detail)
      );
    } finally {
      setLoading(false);
    }
  };

  const riskColor = prediction
    ? getRiskColor(prediction.level)
    : "#94a3b8";

  const inputStyle = {
    width: "100%",
    boxSizing: "border-box",
    padding: "10px",
    background: "#0b111b",
    color: "#e2e8f0",
    border: "1px solid #29364a",
    borderRadius: "7px",
    outline: "none",
    fontSize: "12px",
  };

  const labelStyle = {
    display: "block",
    marginBottom: "6px",
    color: "#94a3b8",
    fontSize: "11px",
  };

  const renderField = (
    name,
    label,
    placeholder = "Enter value",
    step = "any"
  ) => (
    <div>
      <label style={labelStyle}>{label}</label>

      <input
        type="number"
        step={step}
        name={name}
        value={form[name]}
        onChange={handleChange}
        placeholder={placeholder}
        style={inputStyle}
      />
    </div>
  );

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
      {/* HEADER */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
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
            <Gauge size={25} color="#818cf8" />

            <h1
              style={{
                margin: 0,
                fontSize: "25px",
                fontWeight: 750,
              }}
            >
              Predictive Risk
            </h1>
          </div>

          <p
            style={{
              margin: "7px 0 0",
              color: "#94a3b8",
              fontSize: "13px",
            }}
          >
            Request a model-based risk prediction for a network grid.
          </p>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "7px",
            padding: "8px 11px",
            borderRadius: "8px",
            background: "rgba(129,140,248,0.10)",
            border: "1px solid rgba(129,140,248,0.25)",
            color: "#a5b4fc",
            fontSize: "11px",
          }}
        >
          <Brain size={14} />
          ML Prediction Service
        </div>
      </div>

      {/* ERROR */}
      {error && (
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: "10px",
            padding: "13px 15px",
            marginBottom: "20px",
            borderRadius: "9px",
            background: "rgba(239,68,68,0.10)",
            border: "1px solid rgba(239,68,68,0.35)",
            color: "#fca5a5",
            fontSize: "13px",
          }}
        >
          <AlertTriangle
            size={17}
            style={{
              marginTop: "1px",
              flexShrink: 0,
            }}
          />

          <div>
            <div
              style={{
                fontWeight: 700,
                marginBottom: "3px",
              }}
            >
              Prediction failed
            </div>

            <div>{error}</div>
          </div>
        </div>
      )}

      {/* MAIN GRID */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "minmax(320px,0.85fr) minmax(420px,1.15fr)",
          gap: "20px",
          alignItems: "start",
        }}
      >
        {/* INPUT PANEL */}
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
              borderBottom: "1px solid #1f2b3d",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "9px",
              }}
            >
              <Target size={17} color="#818cf8" />

              <h2
                style={{
                  margin: 0,
                  fontSize: "15px",
                }}
              >
                Prediction Input
              </h2>
            </div>

            <p
              style={{
                margin: "6px 0 0",
                color: "#64748b",
                fontSize: "11px",
                lineHeight: 1.5,
              }}
            >
              Provide the feature values used by the deployed
              prediction model.
            </p>
          </div>

          <form
            onSubmit={handlePredict}
            style={{
              padding: "18px",
            }}
          >
            {/* GRID ID */}
            <div style={{ marginBottom: "16px" }}>
              <label
                style={{
                  display: "block",
                  marginBottom: "7px",
                  color: "#cbd5e1",
                  fontSize: "12px",
                  fontWeight: 600,
                }}
              >
                Grid ID *
              </label>

              <input
                type="number"
                min="1"
                name="grid_id"
                value={form.grid_id}
                onChange={handleChange}
                placeholder="Example: 1"
                style={inputStyle}
              />
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "7px",
                marginBottom: "13px",
                color: "#64748b",
                fontSize: "10px",
                textTransform: "uppercase",
                letterSpacing: "0.5px",
              }}
            >
              <Activity size={13} />
              Model Feature Values
            </div>

            {/* FEATURE GRID */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(2,minmax(0,1fr))",
                gap: "13px",
              }}
            >
              {renderField(
                "avg_activity",
                "Average Activity",
                "e.g. 500"
              )}

              {renderField(
                "activity_growth",
                "Activity Growth",
                "e.g. 0.15"
              )}

              {renderField(
                "active_hours",
                "Active Hours",
                "e.g. 12"
              )}

              {renderField(
                "peak_ratio",
                "Peak Ratio",
                "e.g. 1.25"
              )}

              {renderField(
                "variability",
                "Variability",
                "e.g. 0.20"
              )}

              {renderField(
                "internet_share",
                "Internet Share",
                "e.g. 0.45"
              )}

              {renderField(
                "activity_vs_baseline",
                "Activity vs Baseline",
                "e.g. 1.10"
              )}

              {renderField(
                "baseline_gap",
                "Baseline Gap",
                "e.g. 50"
              )}
            </div>

            {/* TIMESTAMP */}
            <div style={{ marginTop: "13px" }}>
              <label style={labelStyle}>
                Feature Timestamp
              </label>

              <input
                type="datetime-local"
                name="feature_timestamp"
                value={form.feature_timestamp}
                onChange={handleChange}
                style={{
                  ...inputStyle,
                  colorScheme: "dark",
                }}
              />
            </div>

            {/* INFO */}
            <div
              style={{
                display: "flex",
                gap: "8px",
                padding: "11px",
                marginTop: "16px",
                borderRadius: "8px",
                background: "rgba(96,165,250,0.07)",
                border:
                  "1px solid rgba(96,165,250,0.18)",
                color: "#94a3b8",
                fontSize: "10px",
                lineHeight: 1.5,
              }}
            >
              <Info
                size={14}
                color="#60a5fa"
                style={{
                  flexShrink: 0,
                  marginTop: "1px",
                }}
              />

              <span>
                These values are sent directly to the prediction
                service. The result is a model-generated risk
                indicator, not a guaranteed outcome.
              </span>
            </div>

            {/* SUBMIT */}
            <button
              type="submit"
              disabled={loading}
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
                marginTop: "18px",
                padding: "12px",
                border: "none",
                borderRadius: "8px",
                background: loading
                  ? "#373d58"
                  : "#6366f1",
                color: "#ffffff",
                cursor: loading
                  ? "not-allowed"
                  : "pointer",
                fontSize: "12px",
                fontWeight: 700,
              }}
            >
              {loading ? (
                <>
                  <Loader2
                    size={15}
                    className="spin"
                  />
                  Running Prediction...
                </>
              ) : (
                <>
                  <Gauge size={15} />
                  Predict Risk
                </>
              )}
            </button>
          </form>
        </div>

        {/* MODEL OUTPUT */}
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
              borderBottom: "1px solid #1f2b3d",
              display: "flex",
              justifyContent: "space-between",
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
                Model Output
              </h2>

              <p
                style={{
                  margin: "5px 0 0",
                  color: "#64748b",
                  fontSize: "11px",
                }}
              >
                Prediction returned by the deployed model.
              </p>
            </div>

            <Brain size={18} color="#818cf8" />
          </div>

          {!prediction ? (
            <div
              style={{
                minHeight: "350px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                padding: "30px",
                textAlign: "center",
              }}
            >
              <div
                style={{
                  width: "58px",
                  height: "58px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  borderRadius: "14px",
                  background:
                    "rgba(129,140,248,0.10)",
                  border:
                    "1px solid rgba(129,140,248,0.20)",
                  marginBottom: "14px",
                }}
              >
                <Gauge
                  size={26}
                  color="#818cf8"
                />
              </div>

              <div
                style={{
                  fontSize: "14px",
                  fontWeight: 650,
                }}
              >
                No prediction yet
              </div>

              <div
                style={{
                  maxWidth: "330px",
                  marginTop: "7px",
                  color: "#64748b",
                  fontSize: "11px",
                  lineHeight: 1.5,
                }}
              >
                Enter the required model features and submit
                the request to retrieve the prediction.
              </div>
            </div>
          ) : (
            <div
              style={{
                padding: "18px",
              }}
            >
              {/* RISK LEVEL */}
              <div
                style={{
                  padding: "20px",
                  borderRadius: "11px",
                  background:
                    getRiskBackground(
                      prediction.level
                    ),
                  border: `1px solid ${riskColor}35`,
                  textAlign: "center",
                }}
              >
                <div
                  style={{
                    color: "#94a3b8",
                    fontSize: "10px",
                    textTransform: "uppercase",
                    letterSpacing: "0.8px",
                  }}
                >
                  Predicted Risk Level
                </div>

                <div
                  style={{
                    marginTop: "9px",
                    color: riskColor,
                    fontSize: "30px",
                    fontWeight: 800,
                    letterSpacing: "0.5px",
                  }}
                >
                  {prediction.level}
                </div>
              </div>

              {/* SCORE + MODEL */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(2,minmax(0,1fr))",
                  gap: "12px",
                  marginTop: "13px",
                }}
              >
                <div
                  style={{
                    padding: "16px",
                    background: "#0c121d",
                    border: "1px solid #202c3e",
                    borderRadius: "9px",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "7px",
                      color: "#64748b",
                      fontSize: "10px",
                    }}
                  >
                    <Activity size={13} />
                    RISK SCORE
                  </div>

                  <div
                    style={{
                      marginTop: "9px",
                      fontSize: "24px",
                      fontWeight: 750,
                      color: "#f8fafc",
                    }}
                  >
                    {formatScore(prediction.score)}
                  </div>
                </div>

                <div
                  style={{
                    padding: "16px",
                    background: "#0c121d",
                    border: "1px solid #202c3e",
                    borderRadius: "9px",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "7px",
                      color: "#64748b",
                      fontSize: "10px",
                    }}
                  >
                    <Brain size={13} />
                    MODEL VERSION
                  </div>

                  <div
                    style={{
                      marginTop: "9px",
                      fontSize: "16px",
                      fontWeight: 700,
                      color: "#c7d2fe",
                    }}
                  >
                    {prediction.version}
                  </div>
                </div>
              </div>

              {/* GRID */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "13px 14px",
                  marginTop: "12px",
                  background: "#0c121d",
                  border: "1px solid #202c3e",
                  borderRadius: "9px",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  <Target
                    size={14}
                    color="#60a5fa"
                  />

                  <span
                    style={{
                      color: "#64748b",
                      fontSize: "11px",
                    }}
                  >
                    Target Grid
                  </span>
                </div>

                <span
                  style={{
                    fontFamily:
                      "JetBrains Mono, monospace",
                    fontSize: "12px",
                    fontWeight: 700,
                  }}
                >
                  #{prediction.gridId}
                </span>
              </div>

              {/* DISCLAIMER */}
              <div
                style={{
                  display: "flex",
                  gap: "8px",
                  padding: "12px",
                  marginTop: "14px",
                  borderRadius: "8px",
                  background:
                    "rgba(148,163,184,0.06)",
                  border: "1px solid #202c3e",
                  color: "#64748b",
                  fontSize: "10px",
                  lineHeight: 1.5,
                }}
              >
                <Info
                  size={14}
                  style={{
                    flexShrink: 0,
                  }}
                />

                <span>
                  This result represents the model's estimated
                  risk based on the submitted input. It should
                  not be interpreted as a certain prediction of
                  future network behavior.
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* EXPLANATION SECTION */}
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
            justifyContent: "space-between",
            alignItems: "center",
            borderBottom: "1px solid #1f2b3d",
          }}
        >
          <div>
            <h2
              style={{
                margin: 0,
                display: "flex",
                alignItems: "center",
                gap: "8px",
                fontSize: "15px",
              }}
            >
              <Sparkles
                size={17}
                color="#c084fc"
              />
              Prediction Explanation
            </h2>

            <p
              style={{
                margin: "5px 0 0",
                color: "#64748b",
                fontSize: "11px",
              }}
            >
              Reserved for the future AI explanation phase.
            </p>
          </div>

          <button
            type="button"
            disabled={!prediction}
            onClick={() => {
              if (!prediction) return;

              alert(
                "Explain with AI will be connected during the Claude phase."
              );
            }}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "7px",
              padding: "9px 13px",
              borderRadius: "7px",
              border:
                "1px solid rgba(192,132,252,0.30)",
              background: prediction
                ? "rgba(192,132,252,0.10)"
                : "#0c121d",
              color: prediction
                ? "#d8b4fe"
                : "#475569",
              cursor: prediction
                ? "pointer"
                : "not-allowed",
              fontSize: "11px",
              fontWeight: 650,
            }}
          >
            <Sparkles size={14} />
            Explain with AI
          </button>
        </div>

        <div
          style={{
            padding: "18px",
            display: "grid",
            gridTemplateColumns:
              "repeat(3,minmax(0,1fr))",
            gap: "12px",
          }}
        >
          <div
            style={{
              padding: "14px",
              background: "#0c121d",
              border: "1px solid #202c3e",
              borderRadius: "9px",
            }}
          >
            <CheckCircle2
              size={16}
              color="#818cf8"
            />

            <div
              style={{
                marginTop: "9px",
                fontSize: "12px",
                fontWeight: 650,
              }}
            >
              Model Output
            </div>

            <div
              style={{
                marginTop: "5px",
                color: "#64748b",
                fontSize: "10px",
                lineHeight: 1.5,
              }}
            >
              Risk score, risk level and model version are
              shown directly from the prediction service.
            </div>
          </div>

          <div
            style={{
              padding: "14px",
              background: "#0c121d",
              border: "1px solid #202c3e",
              borderRadius: "9px",
            }}
          >
            <ShieldAlert
              size={16}
              color="#f59e0b"
            />

            <div
              style={{
                marginTop: "9px",
                fontSize: "12px",
                fontWeight: 650,
              }}
            >
              Risk Indicator
            </div>

            <div
              style={{
                marginTop: "5px",
                color: "#64748b",
                fontSize: "10px",
                lineHeight: 1.5,
              }}
            >
              The prediction indicates estimated risk and
              should not be treated as a guaranteed event.
            </div>
          </div>

          <div
            style={{
              padding: "14px",
              background: "#0c121d",
              border: "1px solid #202c3e",
              borderRadius: "9px",
            }}
          >
            <Clock
              size={16}
              color="#60a5fa"
            />

            <div
              style={{
                marginTop: "9px",
                fontSize: "12px",
                fontWeight: 650,
              }}
            >
              AI Explanation
            </div>

            <div
              style={{
                marginTop: "5px",
                color: "#64748b",
                fontSize: "10px",
                lineHeight: 1.5,
              }}
            >
              Future Claude integration can explain why the
              model produced this result.
            </div>
          </div>
        </div>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "7px",
          marginTop: "15px",
          color: "#475569",
          fontSize: "10px",
        }}
      >
        <Info size={12} />

        Predictions are generated by the deployed ML service
        using the submitted network information.
      </div>

      <style>
        {`
          @keyframes spin {
            from {
              transform: rotate(0deg);
            }
            to {
              transform: rotate(360deg);
            }
          }

          .spin {
            animation: spin 1s linear infinite;
          }

          input::placeholder {
            color: #475569;
          }

          input:focus {
            border-color: #6366f1 !important;
          }
        `}
      </style>
    </div>
  );
};

export default Risk;