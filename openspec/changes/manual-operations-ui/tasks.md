## 1. Failing tests

- [x] 1.1 Add approval prerequisite, manual tracking and actor/time tests.
- [x] 1.2 Add cancellation review and unsafe tracking URL tests.
- [x] 1.3 Add INR charge/receipt/correction history tests.
- [x] 1.4 Add public/patient submit/accept/doctor workspace UI tests.
- [x] 1.5 Add forged IDs/revocation/full/HTMX/CSRF/private projection tests.
- [x] 1.6 Observe intended failures before implementation.

## 2. Implementation

- [x] 2.1 Implement manual models/services/migrations/corrections.
- [x] 2.2 Implement grant/MFA-checked forms/views and POST-only mutations.
- [x] 2.3 Add responsive templates/styles and explicit feedback/safety guidance.
- [x] 2.4 Wire queue/calendar/patients/visits/repeats/operations consistently.
- [x] 2.5 Document actual live-data/provider/hosting/restore gates.

## 3. Integrated evidence

- [x] 3.1 Run full PostgreSQL pytest including concurrency and CSRF.
- [x] 3.2 Run migrations/Django/format/types/whitespace checks.
- [ ] 3.3 Strictly validate and archive/sync verified core changes.
- [x] 3.4 Keep WhatsApp pending without live-provider claims.
- [ ] 3.5 Commit and report exact branch/path/evidence and production gates.

Evidence: 73 PostgreSQL tests passed on 2026-10-13; strict typing covered
73 application/migration files. Local public/sign-in pages were inspected at
390px width without horizontal overflow; local CSS/HTMX returned 200 and an
unauthenticated doctor route returned 403. Temporary UI server was stopped.
An actual production check failed as intended with E001/E004/E005 for synthetic
secret, missing provider and unapproved live-data gates.
