import axios from 'axios';
import { supabase } from './supabase';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
});

api.interceptors.request.use(async (config) => {
  if (import.meta.env.VITE_DEMO_MODE === 'true') {
    const demoToken = localStorage.getItem('demo_token');
    if (demoToken) {
      config.headers['X-Demo-Token'] = demoToken;
    }
    return config;
  }
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle global errors here
    if (error.response?.status === 401) {
      // potentially sign out or redirect
    }
    return Promise.reject(error);
  }
);

export default api;
