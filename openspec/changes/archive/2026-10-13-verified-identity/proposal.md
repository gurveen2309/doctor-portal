## Why

Phone control is not patient identity. Card numbers and family membership
cannot safely authorize clinical data.

## What Changes

- Distinct accounts/patients, doctor verification and scoped grants.
- Bounded private OTP with real-provider fail-closed behavior.
- MFA on every doctor/admin/verification route and controlled recovery.
- Current permissions, reviewed phone classification and guardian-at-18 checks.
- Application append-only audit metadata without clinical content.

## Capabilities

### New Capabilities

- `verified-identity`: identity, scoped access, secure sign-in and private audit.

### Modified Capabilities

None.

## Impact

Requires verified foundation. Adds `accounts/`, `patients/`, `audit/`,
migrations, sign-in templates and tests. No Aadhaar or automatic card matching.

## Execution Status

Pending draft. No identity/authentication implementation or test evidence.
