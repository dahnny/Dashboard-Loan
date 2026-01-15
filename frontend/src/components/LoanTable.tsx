import type { Loan } from "../types";

interface LoanTableProps {
  loans: Loan[];
  selectedLoanId?: string;
  onSelect: (loan: Loan) => void;
}

export function LoanTable({ loans, selectedLoanId, onSelect }: LoanTableProps) {
  return (
    <div className="table">
      <div className="table-row header">
        <div>ID</div>
        <div>Status</div>
        <div>Due date</div>
        <div>Term (weeks)</div>
        <div>Total payable</div>
      </div>
      {loans.map((loan) => (
        <button
          key={loan.id}
          type="button"
          className={`table-row ${selectedLoanId === loan.id ? "active" : ""}`}
          onClick={() => onSelect(loan)}
        >
          <div className="mono">{loan.id.slice(0, 8)}</div>
          <div className={`pill ${loan.status}`}>{loan.status}</div>
          <div>{new Date(loan.due_date).toLocaleDateString()}</div>
          <div>{loan.loan_term_weeks}</div>
          <div>${Number(loan.total_payable).toFixed(2)}</div>
        </button>
      ))}
      {loans.length === 0 && (
        <div className="table-empty">No loans found for this filter.</div>
      )}
    </div>
  );
}
