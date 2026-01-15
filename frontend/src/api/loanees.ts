import { apiGet } from "./client";
import type { Loanee } from "../types";

export async function fetchLoaneesWithLoans(): Promise<Loanee[]> {
  return apiGet<Loanee[]>("/loanees/with-loans");
}
