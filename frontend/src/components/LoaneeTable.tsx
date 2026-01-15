import type { Loanee } from "../types";

interface LoaneeTableProps {
  loanees: Loanee[];
}

export function LoaneeTable({ loanees }: LoaneeTableProps) {
  return (
    <div className="table loanee-table">
      <div className="table-row header">
        <div>Loanee</div>
        <div>Email</div>
        <div>Phone</div>
        <div>Loans</div>
        <div>Next due</div>
      </div>
      {loanees.map((loanee) => {
        const loans = loanee.loans ?? [];
        const nextDue = loans
          .map((loan) => new Date(loan.due_date))
          .sort((a, b) => a.getTime() - b.getTime())[0];
        return (
          <div key={loanee.id} className="table-row">
            <div>
              <div className="mono">{loanee.full_name}</div>
              <div className="muted">{loanee.id.slice(0, 8)}</div>
            </div>
            <div>{loanee.email ?? "-"}</div>
            <div>{loanee.phone_number ?? "-"}</div>
            <div>{loans.length}</div>
            <div>{nextDue ? nextDue.toLocaleDateString() : "-"}</div>
          </div>
        );
      })}
      {loanees.length === 0 && (
        <div className="table-empty">No loanees found.</div>
      )}
    </div>
  );
}
