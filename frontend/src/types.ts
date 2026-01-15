export type LoanStatus = "not_due" | "due" | "paid" | "defaulted";

export interface Loan {
  id: string;
  loanee_id: string;
  amount: string;
  loan_term_weeks: number;
  surcharge: string;
  penalty: string;
  due_date: string;
  status: LoanStatus;
  auto_debit_enabled: boolean;
  total_payable: string;
  created_at: string;
  updated_at: string;
}

export interface LoanSummary {
  id: string;
  amount: string;
  loan_term_weeks: number;
  due_date: string;
  status: LoanStatus;
  total_payable: string;
}

export interface Loanee {
  id: string;
  full_name: string;
  email?: string | null;
  phone_number?: string | null;
  address?: string | null;
  created_at: string;
  updated_at: string;
  loans?: LoanSummary[];
}

export interface Organization {
  id: string;
  name: string;
  email: string;
  address?: string | null;
  phone_number?: string | null;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  email: string;
  created_at: string;
  phone_number?: string | null;
}
