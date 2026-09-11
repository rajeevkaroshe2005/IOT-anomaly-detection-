import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Attach JWT token automatically
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('iot_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for auth expiry
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Don't loop redirect if already on login
      if (!window.location.pathname.includes('/login')) {
        localStorage.removeItem('iot_token');
        localStorage.removeItem('iot_user');
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (username, password) => api.post('/api/auth/login', { username, password }),
  getProfile: () => api.get('/api/auth/me'),
};

export const sensorsAPI = {
  getAll: () => api.get('/api/sensors'),
  getById: (id) => api.get(`/api/sensors/${id}`),
  create: (data) => api.post('/api/sensors', data),
  update: (id, data) => api.put(`/api/sensors/${id}`, data),
  delete: (id) => api.delete(`/api/sensors/${id}`),
  toggle: (id) => api.post(`/api/sensors/${id}/toggle`),
};

export const readingsAPI = {
  getAll: (params) => api.get('/api/readings', { params }),
  getBySensorId: (sensorId, timeframe = '30m', limit = 200) =>
    api.get(`/api/readings/${sensorId}`, { params: { timeframe, limit } }),
  ingest: (data) => api.post('/api/readings/ingest', data),
};

export const anomaliesAPI = {
  getAll: (params) => api.get('/api/anomalies', { params }),
  acknowledge: (id) => api.put(`/api/anomalies/${id}/acknowledge`),
};

export const alertsAPI = {
  getAll: (params) => api.get('/api/alerts', { params }),
  resolve: (id) => api.put(`/api/alerts/${id}/resolve`),
  delete: (id) => api.delete(`/api/alerts/${id}`),
};

export const dashboardAPI = {
  getStats: () => api.get('/api/dashboard/stats'),
};

export const systemAPI = {
  getHealth: () => api.get('/api/system/health'),
  getLogs: (params) => api.get('/api/system/logs', { params }),
  resetDemo: () => api.post('/api/system/reset-demo'),
};

export const simulatorAPI = {
  start: (config) => api.post('/api/simulator/start', config),
  stop: () => api.post('/api/simulator/stop'),
  getStatus: () => api.get('/api/simulator/status'),
  forceAnomaly: (deviceId) => api.post('/api/simulator/force-anomaly', { device_id: deviceId }),
};

export const predictiveAPI = {
  getAnalytics: () => api.get('/api/predictive/analytics'),
  getSensorPrediction: (id) => api.get(`/api/predictive/sensor/${id}`),
};

export const exportAPI = {
  getReadingsCsvUrl: (sensorId = null) => {
    const token = localStorage.getItem('iot_token');
    const base = `${API_BASE_URL}/api/readings/export/csv`;
    const params = new URLSearchParams();
    if (sensorId) params.append('sensor_id', sensorId);
    if (token) params.append('token', token);
    const qs = params.toString();
    return qs ? `${base}?${qs}` : base;
  },
  getAnomaliesCsvUrl: (sensorId = null) => {
    const token = localStorage.getItem('iot_token');
    const base = `${API_BASE_URL}/api/anomalies/export/csv`;
    const params = new URLSearchParams();
    if (sensorId) params.append('sensor_id', sensorId);
    if (token) params.append('token', token);
    const qs = params.toString();
    return qs ? `${base}?${qs}` : base;
  }
};

export default api;
