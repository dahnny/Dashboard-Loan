import { apiPost, setAccessToken } from "./client";
import type { Organization } from "../types";

export interface AuthResponse {
  organization: Organization;
  access_token: string;
  refresh_token: string;
}

export interface SignupPayload {
  name: string;
  email: string;
  password: string;
  confirm_password: string;
  phone_number?: string;
  address?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export async function signup(payload: SignupPayload): Promise<Organization> {
  return apiPost<Organization>("/auth/signup", payload);
}

export async function login(payload: LoginPayload): Promise<AuthResponse> {
  const data = await apiPost<AuthResponse>("/auth/login", payload);
  setAccessToken(data.access_token);
  return data;
}

export function logout() {
  setAccessToken(null);
}
