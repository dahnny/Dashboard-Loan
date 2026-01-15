import type { Loan } from "../types";

interface LoanDetailProps {
  loan?: Loan;
}

export function LoanDetail({ loan }: LoanDetailProps) {
  if (!loan) {
    return (
      <div className="panel empty">
        <h3>Select a loan</h3>
        <p>Click a loan row to view details and actions.</p>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <h3>Loan details</h3>
          <p className="mono">{loan.id}</p>
        </div>
        <span className={`pill ${loan.status}`}>{loan.status}</span>
      </div>
      <div className="detail-grid">
        <div>
          <span>Loanee ID</span>
          <strong className="mono">{loan.loanee_id}</strong>
        </div>
        <div>
          <span>Due date</span>
          <strong>{new Date(loan.due_date).toLocaleDateString()}</strong>
        </div>
        <div>
          <span>Loan term</span>
          <strong>{loan.loan_term_weeks} weeks</strong>
        </div>
        <div>
          <span>Total payable</span>
          <strong>${Number(loan.total_payable).toFixed(2)}</strong>
        </div>
        <div>
          <span>Amount</span>
          <strong>${Number(loan.amount).toFixed(2)}</strong>
        </div>
        <div>
          <span>Auto debit</span>
          <strong>{loan.auto_debit_enabled ? "Enabled" : "Disabled"}</strong>
        </div>
      </div>
      <div className="actions">
        <button type="button" className="primary" disabled>
          Direct debit (coming soon)
        </button>
      </div>
    </div>
  );
}
