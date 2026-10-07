import api from "./api";

export const getNetworkSummary = async () => {
  const response = await api.get("/network/summary");
  return response.data;
};

export const getGridData = async (gridId) => {
  const response = await api.get(`/network/grid/${gridId}`);
  return response.data;
};

export const getHotspots = async (limit = 20) => {
  const response = await api.get("/network/hotspots", {
    params: { limit },
  });
  return response.data;
};

export const getAlerts = async (limit = 20, severity = "ALL") => {
  const params = { limit };

  if (severity !== "ALL") {
    params.severity = severity;
  }

  const response = await api.get("/network/alerts", {
    params,
  });

  return response.data;
};

export const getGridFeatures = async (gridId) => {
  const response = await api.get(`/network/grid/${gridId}/features`);
  return response.data;
};

export const getGridLocation = async (gridId) => {
  const response = await api.get(`/network/grid/${gridId}/location`);
  return response.data;
};

export const getGridNeighbours = async (gridId) => {
  const response = await api.get(`/network/grid/${gridId}/neighbours`);
  return response.data;
};

export const predictNetworkRisk = async (payload) => {
  const response = await api.post("/network/predict-risk", payload);
  return response.data;
};