// src/config/environment.ts — Read VITE env vars with safe defaults.

export const ENV = {
  API_BASE_URL:
    (import.meta as unknown as { env: Record<string, string> }).env?.VITE_API_BASE_URL ??
    "http://localhost:8000/api/v1",
  IS_DEV: import.meta.env?.DEV ?? false,
} as const;
