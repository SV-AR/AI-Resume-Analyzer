import axios from "axios";

const TOKEN_KEY = "sra_token";
export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

const http = axios.create({ baseURL: API_URL, timeout: 120000 });

http.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

http.interceptors.response.use(
  (r) => r,
  (error) => {
    const isAuthCall = error.config?.url?.startsWith("/auth/login") || error.config?.url?.startsWith("/auth/register");
    if (error.response?.status === 401 && !isAuthCall) {
      tokenStore.clear();
      window.dispatchEvent(new Event("sra:logout"));
    }
    return Promise.reject(error);
  }
);

/** Turns any axios error into a message that is safe to show to the user. */
export function errorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (error?.code === "ECONNABORTED") return "The request timed out. Please try again.";
  if (!error?.response) return "Cannot reach the server. Check that the backend is running.";
  return "Something went wrong. Please try again.";
}

export const authApi = {
  register: (data) => http.post("/auth/register", data).then((r) => r.data),
  login: (data) => http.post("/auth/login", data).then((r) => r.data),
  me: () => http.get("/auth/me").then((r) => r.data),
};

export const resumeApi = {
  upload: (file, onProgress) => {
    const form = new FormData();
    form.append("file", file);
    return http
      .post("/resumes/upload", form, {
        onUploadProgress: (e) => onProgress && e.total && onProgress(Math.round((e.loaded * 100) / e.total)),
      })
      .then((r) => r.data);
  },
  list: () => http.get("/resumes").then((r) => r.data),
  get: (id) => http.get(`/resumes/${id}`).then((r) => r.data),
  remove: (id) => http.delete(`/resumes/${id}`),
};

export const jobApi = {
  analyze: (data) => http.post("/jobs/analyze", data).then((r) => r.data),
  list: () => http.get("/jobs").then((r) => r.data),
  get: (id) => http.get(`/jobs/${id}`).then((r) => r.data),
};

export const matchApi = {
  analyze: (data) => http.post("/matching/analyze", data).then((r) => r.data),
  list: () => http.get("/matching").then((r) => r.data),
  get: (id) => http.get(`/matching/${id}`).then((r) => r.data),
};

export const dashboardApi = { get: () => http.get("/dashboard").then((r) => r.data) };
