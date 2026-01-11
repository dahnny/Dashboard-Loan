# Loan Domain Models (Rationale)

This document explains why each field exists in the core loan lifecycle models.

## Shared conventions

- `id`: Primary key for stable references.
- `organization_id`: Multi-tenant safety. Every record belongs to an org; server assigns the default org on creation.
- `created_at`, `updated_at`: Auditability and debugging (who/when in conjunction with `AuditLog`).

## `Organization`

- `name`: Human-readable label.
- `slug`: Stable unique identifier for programmatic lookup (e.g., `default`).

## `Loanee`

- `user_id` (nullable): Optional link to an internal `User` row if the loanee is also a system user.
- `full_name`: Needed for identification and document generation.
- `email`, `phone_number` (nullable): Contact channels for reminders/collections; kept nullable to support partial onboarding.

## `Loan`

- `loanee_id`: Who the loan belongs to.
- `amount`: Principal amount being lent.
- `loan_term_weeks`: Term length used for schedules and reporting.
- `surcharge`: Non-penalty fees (origination/service fees).
- `penalty`: Penalty fees applied for late/default scenarios.
- `due_date`: Date the loan becomes due.
- `status`: Enumerated lifecycle state (state machine; not a free string).
- `auto_debit_enabled`: Whether the system is allowed to attempt automatic collection.
- `total_payable`: Stored derived value for audit stability (principal + fees as-of agreement/recording time). This prevents historical totals changing if surcharge/penalty rules evolve later.

### Loan state machine

Allowed transitions:

- `not_due → due`
- `due → paid`
- `due → defaulted`
- `not_due → paid` (early payment)

All other transitions are rejected by `LoanService`.

## `LoanDocument`

- `loan_id`: Which loan the document belongs to.
- `document_type`: Classification (agreement, statement, ID, etc.).
- `uri`: Storage location (S3/Supabase storage/etc.).
- `checksum` (nullable): Integrity check to detect tampering/corruption.

## `Payment`

- `loan_id`: Which loan the payment applies to.
- `amount`: Amount received.
- `reference` (nullable): Provider reference (transfer id, receipt number) for reconciliation.
- `source`: How it was collected (manual, direct_debit, etc.).

## `DirectDebitMandate`

- `loanee_id`: Who authorized the mandate.
- `provider`: Payment provider name (e.g., GoCardless).
- `mandate_reference`: Provider’s unique identifier.
- `active`: Whether the mandate can currently be used.

## `AuditLog`

- `actor_user_id` (nullable): System user who performed the action.
- `loan_id` (nullable): Loan context when applicable.
- `action`: Machine-readable event name.
- `from_status`, `to_status` (nullable): Captures state transitions when the event is a transition.
- `message` (nullable): Human-readable context.
