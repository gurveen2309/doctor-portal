## 1. Failing tests

- [x] 1.1 Add synthetic verification/card uniqueness and permission matrix tests.
- [x] 1.2 Add shared adult phone, revocation and guardian birthday boundary tests.
- [x] 1.3 Add OTP expiry/exhaustion/resend/replay and fail-closed provider tests.
- [x] 1.4 Add secret-log/report absence and private audit immutability tests.
- [x] 1.5 Add password-only denial, verified MFA and controlled recovery tests.
- [x] 1.6 Observe intended failures before production code.

## 2. Implementation

- [x] 2.1 Implement account/patient/grant/audit models and migrations.
- [x] 2.2 Implement doctor verification, card assignment and current permission checks.
- [x] 2.3 Integrate maintained MFA and narrow OTP delivery adapter.
- [x] 2.4 Implement CSRF-protected sign-in and doctor verification/grant routes.
- [x] 2.5 Protect any enabled admin with MFA or leave it disabled.

## 3. Evidence

- [x] 3.1 Run targeted identity/permission/auth/audit tests on PostgreSQL.
- [x] 3.2 Run migration/Django/format/type/whitespace checks.
- [ ] 3.3 Strictly validate, archive/sync verified capability and commit.
- [x] 3.4 Document actual provider and recovery production gates.

Evidence: identity, OTP/concurrency, doctor auth/setup, error-privacy,
invariant and UI suites. Full PostgreSQL acceptance: 73 passed on 2026-10-13.
Provider delivery remains synthetic; no live-provider or legal readiness claim.
