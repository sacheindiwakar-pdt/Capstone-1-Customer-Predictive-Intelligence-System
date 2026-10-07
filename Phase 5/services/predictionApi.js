import api from "./api";

export const predictRisk = async (data) => {
  const response = await api.post("/network/predict-risk", data);
  return response.data;
};