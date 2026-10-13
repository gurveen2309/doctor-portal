## 1. Failing tests

- [ ] 1.1 Add received/type/age/flag and private-reason tests.
- [ ] 1.2 Add same/different-payload duplicate-key tests.
- [ ] 1.3 Add original-time confirmation and alternative acceptance tests.
- [ ] 1.4 Add current availability/closure/aware time/half-open overlap tests.
- [ ] 1.5 Add pending/failed replacement preserving original booking tests.
- [ ] 1.6 Add mixed-channel real PostgreSQL concurrency and proposal replay tests.
- [ ] 1.7 Observe intended failures before implementation.

## 2. Implementation

- [ ] 2.1 Implement profile/windows/closures/singleton calendar models.
- [ ] 2.2 Implement request/proposal/appointment models and migrations.
- [ ] 2.3 Add active-range PostgreSQL exclusion constraint.
- [ ] 2.4 Implement grant/MFA checks, duplicate suppression and locking services.
- [ ] 2.5 Wire all channels to the same calendar services and CSRF routes.

## 3. Evidence

- [ ] 3.1 Run intake/calendar/concurrency tests and inspect competing outcomes.
- [ ] 3.2 Verify availability edits never silently move/cancel bookings.
- [ ] 3.3 Run migration/Django/format/type/whitespace checks.
- [ ] 3.4 Strictly validate, archive/sync verified capability and commit.
