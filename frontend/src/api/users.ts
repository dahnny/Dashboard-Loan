import { apiGet } from "./client";
import type { User } from "../types";

export async function fetchUsers(): Promise<User[]> {
  return apiGet<User[]>("/users");
}
