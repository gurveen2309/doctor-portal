## 1. Failing tests

- [x] 1.1 Add received/type/age/flag and private-reason tests.
- [x] 1.2 Add same/different-payload duplicate-key tests.
- [x] 1.3 Add original-time confirmation and alternative acceptance tests.
- [x] 1.4 Add current availability/closure/aware time/half-open overlap tests.
- [x] 1.5 Add pending/failed replacement preserving original booking tests.
- [x] 1.6 Add mixed-channel real PostgreSQL concurrency and proposal replay tests.
- [x] 1.7 Observe intended failures before implementation.

## 2. Implementation

- [x] 2.1 Implement profile/windows/closures/singleton calendar models.
- [x] 2.2 Implement request/proposal/appointment models and migrations.
- [x] 2.3 Add active-range PostgreSQL exclusion constraint.
- [x] 2.4 Implement grant/MFA checks, duplicate suppression and locking services.
- [x] 2.5 Wire all channels to the same calendar services and CSRF routes.

## 3. Evidence

- [x] 3.1 Run intake/calendar/concurrency tests and inspect competing outcomes.
- [x] 3.2 Verify availability edits never silently move/cancel bookings.
- [x] 3.3 Run migration/Django/format/type/whitespace checks.
- [x] 3.4 Strictly validate, archive/sync verified capability and commit.

Evidence: calendar, invariants, review-regression and UI suites, including
independent PostgreSQL confirmation/cancellation contenders and all channels.
Full PostgreSQL acceptance: 73 passed on 2026-10-13; no SQLite evidence.
Implementation commit: ad1c6a5. CLI archive/sync performed on 2026-10-13.
