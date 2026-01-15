import { apiGet } from "./client";
import type { Loan } from "../types";

export interface LoanFilters {
  status?: string;
  due_from?: string;
  due_to?: string;
  loan_term_weeks?: string;
  loanee_email?: string;
  payment_due?: string;
}

export async function fetchLoans(filters: LoanFilters): Promise<Loan[]> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      params.set(key, value);
    }
  });
  return apiGet<Loan[]>("/loans", params);
}

export async function fetchLoanById(loanId: string): Promise<Loan> {
  return apiGet<Loan>(`/loans/${loanId}`);
}

export async function fetchLoansByLoaneeEmail(email: string): Promise<Loan[]> {
  const params = new URLSearchParams({ email });
  return apiGet<Loan[]>("/loans/by-loanee", params);
}
