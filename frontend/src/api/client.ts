const DEFAULT_BASE_URL = "http://localhost:8000/api/v1";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? DEFAULT_BASE_URL;

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

const ACCESS_TOKEN_KEY = "loan_dashboard_access_token";

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string | null) {
  if (token) {
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
  } else {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    if (response.status === 401) {
      setAccessToken(null);
    }
    const text = await response.text();
    throw new ApiError(text || response.statusText, response.status);
  }
  return (await response.json()) as T;
}

function buildHeaders(): HeadersInit {
  const token = getAccessToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function apiGet<T>(path: string, params?: URLSearchParams): Promise<T> {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (params) {
    url.search = params.toString();
  }
  const response = await fetch(url.toString(), {
    headers: buildHeaders(),
  });
  return handleResponse<T>(response);
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(body),
  });
  return handleResponse<T>(response);
}
