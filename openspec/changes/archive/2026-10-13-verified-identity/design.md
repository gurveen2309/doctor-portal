## Context

OTP establishes phone possession, not exclusivity or patient identity.
Shared phones, delegation and minors need different scope rules.

## Goals / Non-Goals

Goals: verified identity/grants, immediate authorization, MFA and private audit.
Non-goals: family-wide access, Aadhaar, staff roles or automatic record matching.

## Decisions

Accounts have unique normalized phone and doctor-reviewed unreviewed/shared/
private classification. Doctor role does not follow from generic staff flags.
Patients have separate doctor-verification metadata and unique card numbers.
Preserve existing cards; generate new identifiers with uniqueness and bounded
collision retries, never access proof.

`AccessGrant` binds account/patient, explicit scopes, relationship, verifier/
time and revocation actor/time. Verification/classification/grant services
require doctor MFA and lock affected rows. Accounts cannot self-upgrade.

`require_doctor(actor)` consumes a user with maintained-library MFA
verification. `require_access(actor, patient, scope)` evaluates current
database grant, patient verification, reviewed phone classification,
clinic-local age and restoration access suspension, raising `PermissionDenied`.
Do not cache grant decisions in the session. Use the same checks for full,
direct, HTMX and future JSON surfaces.
At patient object view boundaries, expected access denial becomes the same 404
as an absent ID. Service permission errors remain explicit; role/MFA checks
run before lookup on doctor-only routes.

Adult clinical access needs reviewed private phone and verified personal
adult clinical grant. Guardians need child DOB and verified relationship;
clinical scope ends at 18 without inferring a new adult grant. For a leap-day
DOB, use a conservative February 28 access cutoff in a non-leap eighteenth
year; test that boundary and include it in the guardian-process review before
real patient data. This is a portal access policy, not a legal-age assertion.
An administrative delegation is never a guardian clinical grant.

OTP stores hashes, expiry, bounded attempts and consumption under lock.
Resend/account/source limits cannot trust arbitrary forwarded headers.
Only test fixtures inject in-memory delivery. Provider failure is explicit,
not console output or a fake success. Codes/hashes are not logged.
Default reporting hides all request values, locals, user representations and
exception payloads, including unexpected adapter failures. Log severity/status,
failure type and source locations remain observable. This deliberately trades
verbose diagnostics for private-by-default error handling.

Use maintained Django MFA components after compatibility verification. Every
doctor surface and enabled admin must enforce MFA; otherwise disable admin.
Recovery is controlled and audited, not a public role-switch bypass.

Audit events pair transactionally with decisions and store actor/action/
entity type/ID/time, never medical/OTP/address text. Supported application
update/delete paths are prohibited; database-admin tamper-proofing is not claimed.

## Risks / Trade-offs

Private-phone classification is reviewed attestation, not proof from OTP.
Current database permission checks cost queries but ensure immediate revocation.
Runtime age/restoration checks avoid unsafe reliance on periodic jobs.

## Migration Plan

Create account/card/grant/audit migrations. Gradually migrate active verified
patients preserving identifiers; no OCR/full historical transcription.

## Verification

Test scope/classification/relationship/age matrix, existing-session revocation,
card-only denial, OTP expiry/replay/throttling, password-only doctor denial,
recovery and audit privacy. Unauthorized record IDs disclose no clinical data.
