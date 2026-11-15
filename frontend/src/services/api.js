import axios from 'axios';
const api = axios.create({ baseURL: "https://ai-study-assistant-api-eklz.onrender.com/api" });
api.interceptors.request.use(config => {
  const token = localStorage.getItem('study_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
export default api;
