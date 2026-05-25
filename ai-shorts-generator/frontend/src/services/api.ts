import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 120_000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor ─────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('api_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Response interceptor ────────────────────
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const message =
      err.response?.data?.detail ?? err.message ?? 'Unknown error';
    return Promise.reject(new Error(message));
  }
);

export default api;
