## 1. Failing tests

- [ ] 1.1 Add synthetic verification/card uniqueness and permission matrix tests.
- [ ] 1.2 Add shared adult phone, revocation and guardian birthday boundary tests.
- [ ] 1.3 Add OTP expiry/exhaustion/resend/replay and fail-closed provider tests.
- [ ] 1.4 Add secret-log absence and private audit immutability tests.
- [ ] 1.5 Add password-only denial, verified MFA and controlled recovery tests.
- [ ] 1.6 Observe intended failures before production code.

## 2. Implementation

- [ ] 2.1 Implement account/patient/grant/audit models and migrations.
- [ ] 2.2 Implement doctor verification, card assignment and current permission checks.
- [ ] 2.3 Integrate maintained MFA and narrow OTP delivery adapter.
- [ ] 2.4 Implement CSRF-protected sign-in and doctor verification/grant routes.
- [ ] 2.5 Protect any enabled admin with MFA or leave it disabled.

## 3. Evidence

- [ ] 3.1 Run targeted identity/permission/auth/audit tests on PostgreSQL.
- [ ] 3.2 Run migration/Django/format/type/whitespace checks.
- [ ] 3.3 Strictly validate, archive/sync verified capability and commit.
- [ ] 3.4 Document actual provider and recovery production gates.
