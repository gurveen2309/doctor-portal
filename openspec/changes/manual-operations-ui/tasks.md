## 1. Failing tests

- [ ] 1.1 Add approval prerequisite, manual tracking and actor/time tests.
- [ ] 1.2 Add cancellation review and unsafe tracking URL tests.
- [ ] 1.3 Add INR charge/receipt/correction history tests.
- [ ] 1.4 Add public/patient submit/accept/doctor workspace UI tests.
- [ ] 1.5 Add forged IDs/revocation/full/HTMX/CSRF/private projection tests.
- [ ] 1.6 Observe intended failures before implementation.

## 2. Implementation

- [ ] 2.1 Implement manual models/services/migrations/corrections.
- [ ] 2.2 Implement grant/MFA-checked forms/views and POST-only mutations.
- [ ] 2.3 Add responsive templates/styles and explicit feedback/safety guidance.
- [ ] 2.4 Wire queue/calendar/patients/visits/repeats/operations consistently.
- [ ] 2.5 Document actual live-data/provider/hosting/restore gates.

## 3. Integrated evidence

- [ ] 3.1 Run full PostgreSQL pytest including concurrency and CSRF.
- [ ] 3.2 Run migrations/Django/format/types/whitespace checks.
- [ ] 3.3 Strictly validate and archive/sync verified core changes.
- [ ] 3.4 Keep WhatsApp pending without live-provider claims.
- [ ] 3.5 Commit and report exact branch/path/evidence and production gates.
