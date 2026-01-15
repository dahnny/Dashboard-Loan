import { useMemo } from "react";
import type { LoanFilters } from "../api/loans";

interface LoanFiltersProps {
  filters: LoanFilters;
  onChange: (next: LoanFilters) => void;
}

const statusOptions = [
  { label: "Any status", value: "" },
  { label: "Not due", value: "not_due" },
  { label: "Due", value: "due" },
  { label: "Paid", value: "paid" },
  { label: "Defaulted", value: "defaulted" },
];

export function LoanFilters({ filters, onChange }: LoanFiltersProps) {
  const normalized = useMemo(() => ({
    status: filters.status ?? "",
    loan_term_weeks: filters.loan_term_weeks ?? "",
    loanee_email: filters.loanee_email ?? "",
    due_from: filters.due_from ?? "",
    due_to: filters.due_to ?? "",
    payment_due: filters.payment_due ?? "",
  }), [filters]);

  return (
    <div className="filters">
      <div className="field">
        <label htmlFor="status">Status</label>
        <select
          id="status"
          value={normalized.status}
          onChange={(event) =>
            onChange({ ...filters, status: event.target.value || undefined })
          }
        >
          {statusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="loan-term">Loan term (weeks)</label>
        <input
          id="loan-term"
          type="number"
          min={1}
          value={normalized.loan_term_weeks}
          onChange={(event) =>
            onChange({
              ...filters,
              loan_term_weeks: event.target.value || undefined,
            })
          }
          placeholder="e.g. 12"
        />
      </div>
      <div className="field">
        <label htmlFor="email">Loanee email</label>
        <input
          id="email"
          type="email"
          value={normalized.loanee_email}
          onChange={(event) =>
            onChange({
              ...filters,
              loanee_email: event.target.value || undefined,
            })
          }
          placeholder="loanee@example.com"
        />
      </div>
      <div className="field">
        <label htmlFor="due-from">Due from</label>
        <input
          id="due-from"
          type="date"
          value={normalized.due_from}
          onChange={(event) =>
            onChange({ ...filters, due_from: event.target.value || undefined })
          }
        />
      </div>
      <div className="field">
        <label htmlFor="due-to">Due to</label>
        <input
          id="due-to"
          type="date"
          value={normalized.due_to}
          onChange={(event) =>
            onChange({ ...filters, due_to: event.target.value || undefined })
          }
        />
      </div>
      <div className="field checkbox">
        <label htmlFor="payment-due">
          <input
            id="payment-due"
            type="checkbox"
            checked={normalized.payment_due === "true"}
            onChange={(event) =>
              onChange({
                ...filters,
                payment_due: event.target.checked ? "true" : undefined,
              })
            }
          />
          Payment due only
        </label>
      </div>
    </div>
  );
}
