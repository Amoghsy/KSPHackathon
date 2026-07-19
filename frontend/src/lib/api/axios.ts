// src/lib/api/axios.ts — Configured Axios instance for the whole application.

import axios, { type AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from "axios";
import { ENV } from "@/config/environment";

// ─── Create Instance ────────────────────────────────────────────────────────

export const apiClient = axios.create({
  baseURL: ENV.API_BASE_URL,
  timeout: 90_000, // 90s default — LLM calls need more time
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// ─── Request Interceptor ────────────────────────────────────────────────────

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Inject Authorization header from Zustand persisted store
    try {
      const raw = localStorage.getItem("cia-auth");
      if (raw) {
        const parsed = JSON.parse(raw) as { state?: { token?: string } };
        const token = parsed?.state?.token;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      }
    } catch {
      // ignore parse errors
    }

    if (ENV.IS_DEV) {
      console.debug(`[API] ➜ ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
    }

    return config;
  },
  (error: AxiosError) => {
    console.error("[API] Request error:", error.message);
    return Promise.reject(error);
  },
);

// ─── Response Interceptor ───────────────────────────────────────────────────

apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    if (ENV.IS_DEV) {
      console.debug(`[API] ✓ ${response.status} ${response.config.url}`);
    }
    return response;
  },
  async (error: AxiosError) => {
    const status = error.response?.status;
    const url = error.config?.url ?? "";

    if (ENV.IS_DEV) {
      console.error(`[API] ✗ ${status ?? "NETWORK"} ${url}`, error.message);
    }

    // 401 — clear stored auth and redirect to login
    if (status === 401) {
      try {
        localStorage.removeItem("cia-auth");
      } catch (e) {
        console.warn("Storage cleanup failed:", e);
      }
      // Only redirect if we're in a browser context
      if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
        window.location.href = "/login";
      }
    }

    // 403 and DISTRICT_NOT_AUTHORIZED — trigger access request modal globally
    if (status === 403) {
      const detail = (error.response?.data as Record<string, unknown>)?.detail as Record<string, unknown> | undefined;
      if (detail && typeof detail === "object" && detail["code"] === "DISTRICT_NOT_AUTHORIZED") {
        if (typeof window !== "undefined") {
          window.dispatchEvent(new CustomEvent("district-not-authorized", { detail }));
        }
      }
    }


    // 500 — log server errors
    if (status === 500) {
      console.error("[API] Server error at", url, error.response?.data);
    }

    // No network — helpful message
    if (!error.response) {
      console.error("[API] Network error — backend may be unreachable:", error.message);
    }

    return Promise.reject(error);
  },
);

// ─── Typed Helper Wrappers ──────────────────────────────────────────────────

export async function apiGet<T>(path: string, params?: Record<string, unknown>): Promise<T> {
  const { data } = await apiClient.get<T>(path, { params });
  return data;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const { data } = await apiClient.post<T>(path, body);
  return data;
}

/** Use for LLM-backed endpoints (chat) that can take 60–90 s. */
export async function apiPostChat<T>(path: string, body?: unknown): Promise<T> {
  const { data } = await apiClient.post<T>(path, body, { timeout: 120_000 });
  return data;
}

export async function apiPatch<T>(path: string, body?: unknown): Promise<T> {
  const { data } = await apiClient.patch<T>(path, body);
  return data;
}

export async function apiDelete<T>(path: string): Promise<T> {
  const { data } = await apiClient.delete<T>(path);
  return data;
}
