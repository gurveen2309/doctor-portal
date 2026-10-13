## Context

Portal records do not prove courier delivery or bank receipt. Physical
cancellation is a reviewed decision, not an automatic reversal.

## Goals / Non-Goals

Goals: usable core, manual history/corrections and visible errors.
Non-goals: real clinic facts, external integrations, refunds, automation/deploy.

## Decisions

Fulfillment references approved repeat. Doctor services check approval under
lock before preparation/dispatch and record actor/time. Pickup/delivery is
explicit; address collected only where needed. Tracking is manual; links must
be HTTPS and reject credential-bearing/unsafe URLs.

Post-preparation/dispatch patient cancellation creates doctor review, retaining
physical history. No automatic courier reversal or refund.

Charges use decimal INR and explicit consultation/medicine/delivery category.
Receipt entries denote external cash/UPI, actor/time and correction linkage.
Reject invalid amounts; preserve old/correction entries and recompute balances
transactionally. Never imply bank verification or execute refund.

Use forms/templates with selective progressive HTMX. `templates/base.html`
shows navigation and emergency/unmonitored guidance. Patient selectors check
current grants and allowlisted fields. Doctor queue/calendar/verification/
visits/repeats/operations require MFA.

Every mutation requires POST+CSRF, including HTMX. Cross-record IDs require
authorization. Errors are explicit and private, not success-shaped fallbacks.
Public facts are configured; synthetic fixtures never become clinic content.

`docs/production-gates.md` records required provider/privacy/practice/dispensing/
retention/hosting/backup/recovery reviews. No invented policies, costs or
restore evidence. An actual restore invalidates sessions and suspends patient
access/sending pending grant/action reconciliation.

## Risks / Trade-offs

Manual entry needs correction history. Third-party tracking is not authoritative
portal delivery proof. Synthetic tests do not establish production readiness.

## Migration Plan

Create manual tables/constraints; no real data or external transactions.

## Verification

Test no unapproved dispatch, reviewed cancellation, HTTPS links, external
money semantics, correction history, privacy, CSRF and full/HTMX core flows.
Run complete PostgreSQL acceptance before archive or completion claims.
