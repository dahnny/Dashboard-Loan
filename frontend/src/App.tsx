import { useCallback, useEffect, useMemo, useState } from "react";
import "./styles.css";
import { fetchLoanById, fetchLoans } from "./api/loans";
import { fetchLoaneesWithLoans } from "./api/loanees";
import type { Loan, Loanee, Organization } from "./types";
import { LoanFilters } from "./components/LoanFilters";
import { LoanTable } from "./components/LoanTable";
import { LoanDetail } from "./components/LoanDetail";
import { ApiError, getAccessToken } from "./api/client";
import { LoaneeTable } from "./components/LoaneeTable";
import type { LoanFilters as LoanFiltersState } from "./api/loans";
import { login, logout, signup } from "./api/auth";

const DEFAULT_FILTERS: LoanFiltersState = {
  status: "",
  loan_term_weeks: "",
  loanee_email: "",
  due_from: "",
  due_to: "",
  payment_due: "",
};

type TabKey = "loans" | "loanees";
type AuthMode = "login" | "signup";

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>("loans");
  const [loans, setLoans] = useState<Loan[]>([]);
  const [selectedLoan, setSelectedLoan] = useState<Loan | undefined>(undefined);
  const [loanFilters, setLoanFilters] = useState<LoanFiltersState>(DEFAULT_FILTERS);
  const [loanees, setLoanees] = useState<Loanee[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [authOrganization, setAuthOrganization] = useState<Organization | null>(null);
  const [authForm, setAuthForm] = useState({
    name: "",
    email: "",
    password: "",
    confirm_password: "",
    phone_number: "",
    address: "",
  });

  const normalizedFilters = useMemo(() => {
    const cleaned: LoanFiltersState = {};
    Object.entries(loanFilters).forEach(([key, value]) => {
      if (value) {
        cleaned[key as keyof LoanFiltersState] = value;
      }
    });
    return cleaned;
  }, [loanFilters]);

  const loadLoans = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchLoans(normalizedFilters);
      setLoans(data);
      if (selectedLoan) {
        const updated = data.find((loan) => loan.id === selectedLoan.id);
        setSelectedLoan(updated ?? undefined);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load loans.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [normalizedFilters, selectedLoan]);

  const loadLoanees = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchLoaneesWithLoans();
      setLoanees(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load loanees.");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!getAccessToken()) {
      return;
    }
    if (activeTab === "loans") {
      loadLoans();
    } else {
      loadLoanees();
    }
  }, [activeTab, loadLoans, loadLoanees]);

  const handleSelectLoan = useCallback(async (loan: Loan) => {
    setSelectedLoan(loan);
    try {
      const detail = await fetchLoanById(loan.id);
      setSelectedLoan(detail);
    } catch {
      // detail fetch is best-effort; keep list version
    }
  }, []);

  const handleAuthSubmit = useCallback(async () => {
    setError(null);
    setIsLoading(true);
    try {
      if (authMode === "signup") {
        await signup({
          name: authForm.name,
          email: authForm.email,
          password: authForm.password,
          confirm_password: authForm.confirm_password,
          phone_number: authForm.phone_number || undefined,
          address: authForm.address || undefined,
        });
      }
      const data = await login({
        email: authForm.email,
        password: authForm.password,
      });
      setAuthOrganization(data.organization);
      setAuthForm({
        name: "",
        email: "",
        password: "",
        confirm_password: "",
        phone_number: "",
        address: "",
      });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Authentication failed.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [authForm, authMode]);

  const handleLogout = useCallback(() => {
    logout();
    setAuthOrganization(null);
    setLoans([]);
    setLoanees([]);
    setSelectedLoan(undefined);
  }, []);

  const isAuthenticated = Boolean(getAccessToken());

  if (!isAuthenticated) {
    return (
      <div className="app landing">
        <main className="landing-grid">
          <section className="hero">
            <span className="badge">LoanOps Dashboard</span>
            <h1>Stay on top of loan performance in real time.</h1>
            <p>
              Monitor active loans, payment due windows, and user activity in one
              secure dashboard. Built for operational teams that need clarity fast.
            </p>
            <div className="hero-stats">
              <div>
                <strong>Realtime visibility</strong>
                <span>Track due payments and statuses.</span>
              </div>
              <div>
                <strong>Secure access</strong>
                <span>Token-based authentication baked in.</span>
              </div>
              <div>
                <strong>Action-ready</strong>
                <span>Prepare direct debit actions.</span>
              </div>
            </div>
          </section>
          <section className="panel auth-card">
            <div className="auth-tabs">
              <button
                type="button"
                className={authMode === "login" ? "active" : ""}
                onClick={() => setAuthMode("login")}
              >
                Log in
              </button>
              <button
                type="button"
                className={authMode === "signup" ? "active" : ""}
                onClick={() => setAuthMode("signup")}
              >
                Sign up
              </button>
            </div>
            <div className="auth-form">
              <label>
                Organization email
                <input
                  type="email"
                  value={authForm.email}
                  onChange={(event) =>
                    setAuthForm((prev) => ({ ...prev, email: event.target.value }))
                  }
                  placeholder="name@company.com"
                />
              </label>
              <label>
                Password
                <input
                  type="password"
                  value={authForm.password}
                  onChange={(event) =>
                    setAuthForm((prev) => ({ ...prev, password: event.target.value }))
                  }
                  placeholder="••••••••"
                />
              </label>
              {authMode === "signup" && (
                <>
                  <label>
                    Organization name
                    <input
                      type="text"
                      value={authForm.name}
                      onChange={(event) =>
                        setAuthForm((prev) => ({ ...prev, name: event.target.value }))
                      }
                      placeholder="Acme Lending"
                    />
                  </label>
                  <label>
                    Confirm password
                    <input
                      type="password"
                      value={authForm.confirm_password}
                      onChange={(event) =>
                        setAuthForm((prev) => ({
                          ...prev,
                          confirm_password: event.target.value,
                        }))
                      }
                    />
                  </label>
                  <label>
                    Phone number (optional)
                    <input
                      type="tel"
                      value={authForm.phone_number}
                      onChange={(event) =>
                        setAuthForm((prev) => ({
                          ...prev,
                          phone_number: event.target.value,
                        }))
                      }
                      placeholder="+1 555 000 1122"
                    />
                  </label>
                  <label>
                    Address (optional)
                    <input
                      type="text"
                      value={authForm.address}
                      onChange={(event) =>
                        setAuthForm((prev) => ({ ...prev, address: event.target.value }))
                      }
                      placeholder="123 Loan Street"
                    />
                  </label>
                </>
              )}
              {error && <div className="alert">{error}</div>}
              <button
                type="button"
                className="primary"
                onClick={handleAuthSubmit}
                disabled={isLoading}
              >
                {isLoading
                  ? "Please wait…"
                  : authMode === "signup"
                    ? "Create account"
                    : "Log in"}
              </button>
            </div>
          </section>
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <header>
        <div>
          <h1>Loan Operations Dashboard</h1>
          <p>Monitor loans, payments due, and system users.</p>
        </div>
        <div className="header-actions">
          {authOrganization?.email && (
            <span className="user-chip">{authOrganization.email}</span>
          )}
          <button type="button" className="ghost" onClick={handleLogout}>
            Log out
          </button>
        </div>
        <div className="tabs">
          <button
            type="button"
            className={activeTab === "loans" ? "active" : ""}
            onClick={() => setActiveTab("loans")}
          >
            Loans
          </button>
          <button
            type="button"
            className={activeTab === "loanees" ? "active" : ""}
            onClick={() => setActiveTab("loanees")}
          >
            Loanees
          </button>
        </div>
      </header>

      {error && <div className="alert">{error}</div>}

      {activeTab === "loans" && (
        <main className="grid">
          <section className="panel">
            <div className="panel-header">
              <h3>Loan filters</h3>
              {isLoading && <span className="status">Loading…</span>}
            </div>
            <LoanFilters filters={loanFilters} onChange={setLoanFilters} />
            <div className="panel-actions">
              <button type="button" onClick={loadLoans} className="primary">
                Apply filters
              </button>
              <button
                type="button"
                onClick={() => setLoanFilters(DEFAULT_FILTERS)}
                className="ghost"
              >
                Reset
              </button>
            </div>
          </section>
          <section className="panel table-panel">
            <div className="panel-header">
              <h3>Loans</h3>
              <span className="status">{loans.length} records</span>
            </div>
            <LoanTable
              loans={loans}
              selectedLoanId={selectedLoan?.id}
              onSelect={handleSelectLoan}
            />
          </section>
          <LoanDetail loan={selectedLoan} />
        </main>
      )}

      {activeTab === "loanees" && (
        <main className="grid single">
          <section className="panel table-panel">
            <div className="panel-header">
              <h3>Loanees</h3>
              {isLoading && <span className="status">Loading…</span>}
            </div>
            <LoaneeTable loanees={loanees} />
          </section>
        </main>
      )}
    </div>
  );
}
