## 1. Failing tests

- [x] 1.1 Add clarification outcomes and authorized missing-info follow-up tests.
- [x] 1.2 Add immutable/sequential/concurrent instruction-revision tests.
- [x] 1.3 Add nullable explicit follow-up/no inferred interval tests.
- [x] 1.4 Add doctor repeat outcomes/actor/time and no timeout/self-approval tests.
- [x] 1.5 Add admin/log/report/audit private-text omission tests.
- [x] 1.6 Observe intended failures before implementation.

## 2. Implementation

- [x] 2.1 Implement clinical models/constraints/migrations.
- [x] 2.2 Implement doctor decisions and immutable revision services.
- [x] 2.3 Implement clinical-grant selectors and CSRF forms/views.
- [x] 2.4 Pair decisions with metadata audit transactionally.

## 3. Evidence

- [x] 3.1 Run clinical/repeat/audit/direct/HTMX/revocation tests.
- [x] 3.2 Run migration/Django/format/type/whitespace checks.
- [x] 3.3 Strictly validate, archive/sync verified capability and commit.

Evidence: clinical, identity/audit, operations, invariant, error-privacy,
review-regression and UI suites. Full PostgreSQL acceptance: 73 passed on
2026-10-13, including independent concurrent instruction revisions.
Implementation commit: ad1c6a5. CLI archive/sync performed on 2026-10-13.
